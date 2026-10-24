"""Stock movements: buying units and putting them back.

The rule this service exists to enforce is that stock can never go negative,
even when several buyers act at the same instant.
"""

from app.models import Vehicle
from app.repositories.vehicle_repository import VehicleRepository
from app.services.exceptions import (
    InsufficientStockError,
    OutOfStockError,
    VehicleNotFoundError,
)


class InventoryService:
    """Purchase and restock operations."""

    def __init__(self, repository: VehicleRepository) -> None:
        self._repository = repository

    def _require(self, vehicle_id: str) -> Vehicle:
        vehicle = self._repository.get(vehicle_id)
        if vehicle is None:
            raise VehicleNotFoundError()
        return vehicle

    def purchase(self, vehicle_id: str, quantity: int = 1) -> Vehicle:
        """Buy `quantity` units, or refuse if that many are not in stock.

        The stock is not read and then written: the repository performs one
        guarded UPDATE and reports how many rows it changed. Zero rows means
        the guard refused, and only then is the vehicle re-read to explain
        why. Checking availability in Python first would be exactly the race
        this design avoids.
        """
        self._require(vehicle_id)

        if self._repository.decrement_stock(vehicle_id, quantity) == 0:
            current = self._require(vehicle_id)
            if current.quantity == 0:
                raise OutOfStockError()
            raise InsufficientStockError(
                f"Only {current.quantity} left in stock"
            )

        return self._require(vehicle_id)

    def restock(self, vehicle_id: str, quantity: int) -> Vehicle:
        """Add `quantity` units to a vehicle's stock."""
        self._require(vehicle_id)
        self._repository.increment_stock(vehicle_id, quantity)
        return self._require(vehicle_id)
