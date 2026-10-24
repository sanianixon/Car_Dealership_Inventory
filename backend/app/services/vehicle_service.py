"""Business rules for the vehicle catalogue.

The service decides what is allowed and what an absent record means; the
repository decides how rows are fetched. Routes depend on this class, not on a
database session.
"""

from typing import Any

from app.models import Vehicle
from app.repositories.vehicle_repository import VehicleRepository
from app.services.exceptions import VehicleNotFoundError


class VehicleService:
    """Catalogue operations."""

    def __init__(self, repository: VehicleRepository) -> None:
        self._repository = repository

    def create(self, make: str, model: str, category: str, price: float, quantity: int) -> Vehicle:
        """Add a vehicle to the catalogue."""
        return self._repository.add(
            Vehicle(
                make=make,
                model=model,
                category=category,
                price=price,
                quantity=quantity,
            )
        )

    def list_all(self) -> list[Vehicle]:
        """Every vehicle, including sold-out ones."""
        return self._repository.list_all()

    def get(self, vehicle_id: str) -> Vehicle:
        """Return one vehicle, or raise if the id is unknown."""
        vehicle = self._repository.get(vehicle_id)
        if vehicle is None:
            raise VehicleNotFoundError()
        return vehicle

    def update(self, vehicle_id: str, changes: dict[str, Any]) -> Vehicle:
        """Apply a partial update to one vehicle.

        Only the keys present in `changes` are written; the schema has already
        guaranteed they are editable fields with valid values.
        """
        vehicle = self.get(vehicle_id)
        for field, value in changes.items():
            setattr(vehicle, field, value)
        return self._repository.save(vehicle)

    def delete(self, vehicle_id: str) -> None:
        """Remove a vehicle, raising if the id is unknown."""
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
        """Find vehicles matching the supplied filters, sold out or not."""
        return self._repository.search(
            make=make,
            model=model,
            category=category,
            min_price=min_price,
            max_price=max_price,
        )
