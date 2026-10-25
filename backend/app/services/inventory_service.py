"""Stock movements: buying a specific car, and taking more cars in.

The rule this service exists to enforce is that a car is sold exactly once,
even when two buyers reach it at the same instant.
"""

from typing import Any

from app.models import Vehicle, VehicleUnit
from app.repositories.vehicle_repository import VehicleRepository
from app.services.exceptions import (
    OutOfStockError,
    UnitNotAvailableError,
    UnitNotFoundError,
)
from app.services.lookup import require_vehicle


class InventoryService:
    """Purchase and restock operations."""

    def __init__(self, repository: VehicleRepository) -> None:
        self._repository = repository

    def purchase(self, vehicle_id: str, unit_id: str | None = None) -> tuple[Vehicle, VehicleUnit]:
        """Buy one car of this model, named or chosen.

        With no unit named, the cheapest available car is taken: that is what
        "buy a Honda City" means on a forecourt, and it keeps the endpoint
        usable by a caller who does not know unit ids.

        The stock is not read and then written. The repository performs one
        guarded UPDATE against the chosen car and reports whether it changed a
        row; zero rows means somebody else claimed it first. Checking
        availability in Python and then writing would be exactly the race this
        design avoids.
        """
        vehicle = require_vehicle(self._repository, vehicle_id)

        if unit_id is not None:
            target = self._require_unit_of(vehicle, unit_id)
            if not target.is_available:
                raise UnitNotAvailableError()
            if self._repository.claim_unit(target.id) == 0:
                # The guard refused: the car sold between choosing it and
                # claiming it. Asking for a specific car means that car, so
                # this is a conflict rather than a reason to offer another.
                raise UnitNotAvailableError()
            return self._listing_with(vehicle_id, target.id)

        available = vehicle.available_units
        if not available:
            raise OutOfStockError()

        # Nobody named a car, so try them cheapest first and take the first one
        # that can still be claimed. Losing the race for one car is not a
        # reason to refuse the sale while others are free: ten buyers asking
        # for "a City" when three are on the lot must result in three sales,
        # not one. Each attempt is guarded, so a car claimed by someone else in
        # the meantime simply fails and the next is tried.
        for candidate in available:
            if self._repository.claim_unit(candidate.id) == 1:
                return self._listing_with(vehicle_id, candidate.id)

        # Every car this buyer could see has been taken by someone else.
        raise OutOfStockError()

    def restock(self, vehicle_id: str, units: list[dict[str, Any]]) -> tuple[Vehicle, list[VehicleUnit]]:
        """Take more cars of this model onto the lot."""
        vehicle = require_vehicle(self._repository, vehicle_id)
        added = self._repository.add_units(vehicle, [VehicleUnit(**unit) for unit in units])
        return require_vehicle(self._repository, vehicle_id), added

    def _require_unit_of(self, vehicle: Vehicle, unit_id: str) -> VehicleUnit:
        """Find a car, insisting it belongs to the listing in the path.

        Without this check a caller could buy any car in the dealership through
        any listing's URL, which would be a confusing audit trail at best.
        """
        for unit in vehicle.units:
            if unit.id == unit_id:
                return unit
        raise UnitNotFoundError()

    def _listing_with(self, vehicle_id: str, unit_id: str) -> tuple[Vehicle, VehicleUnit]:
        """Re-read the listing after a sale and pick the car out of it.

        One query rather than two: the listing is needed anyway for its updated
        stock count, and it carries its units.
        """
        vehicle = require_vehicle(self._repository, vehicle_id)
        return vehicle, next(unit for unit in vehicle.units if unit.id == unit_id)
