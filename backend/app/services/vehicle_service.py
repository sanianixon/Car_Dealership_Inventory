"""Business rules for the vehicle catalogue.

The service decides what is allowed and what an absent record means; the
repository decides how rows are fetched. Routes depend on this class, not on a
database session.
"""

from typing import Any

from app.models import Vehicle, VehicleUnit
from app.repositories.vehicle_repository import VehicleRepository
from app.services.exceptions import DuplicateListingError
from app.services.lookup import require_vehicle


class VehicleService:
    """Catalogue operations on listings."""

    def __init__(self, repository: VehicleRepository) -> None:
        self._repository = repository

    def create(self, make: str, model: str, category: str, units: list[dict[str, Any]]) -> Vehicle:
        """Add a listing together with the cars that make it up.

        A model is not stocked without actual cars, so the schema requires at
        least one unit and this method stores them in the same transaction as
        the listing: a listing with no cars would show as sold out the moment
        it was created.
        """
        if self._repository.find_by_model(make, model) is not None:
            raise DuplicateListingError(f"{make} {model} is already listed")

        vehicle = Vehicle(
            make=make,
            model=model,
            category=category,
            units=[VehicleUnit(**unit) for unit in units],
        )
        return self._repository.add(vehicle)

    def list_all(self) -> list[Vehicle]:
        """Every listing, including those with nothing left in stock."""
        return self._repository.list_all()

    def get(self, vehicle_id: str) -> Vehicle:
        """Return one listing with its cars, or raise if the id is unknown."""
        return require_vehicle(self._repository, vehicle_id)

    def update(self, vehicle_id: str, changes: dict[str, Any]) -> Vehicle:
        """Apply a partial update to a listing's own fields.

        A car's year, colour, price or history is not changed here: those
        belong to the unit, not to the model.
        """
        vehicle = self.get(vehicle_id)

        make = changes.get("make", vehicle.make)
        model = changes.get("model", vehicle.model)
        if (make, model) != (vehicle.make, vehicle.model):
            clash = self._repository.find_by_model(make, model)
            if clash is not None and clash.id != vehicle.id:
                raise DuplicateListingError(f"{make} {model} is already listed")

        for field, value in changes.items():
            setattr(vehicle, field, value)
        return self._repository.save(vehicle)

    def delete(self, vehicle_id: str) -> None:
        """Remove a listing and the cars it holds."""
        self._repository.delete(self.get(vehicle_id))

    def search(
        self,
        *,
        make: str | None = None,
        model: str | None = None,
        category: str | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
    ) -> list[Vehicle]:
        """Find listings matching the supplied filters."""
        return self._repository.search(
            make=make,
            model=model,
            category=category,
            min_price=min_price,
            max_price=max_price,
        )
