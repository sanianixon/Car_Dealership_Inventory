"""Business rules for the vehicle catalogue.

The service decides what is allowed and what an absent record means; the
repository decides how rows are fetched. Routes depend on this class, not on a
database session.
"""

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
