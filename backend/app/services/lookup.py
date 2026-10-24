"""Shared lookup helper for the service layer.

The repository returns None for an unknown id, which is the right answer for
data access: absence is not its business. Deciding that absence is an error is
a rule, so it lives here, in one place, rather than being repeated by every
service that needs a vehicle.
"""

from app.models import Vehicle
from app.repositories.vehicle_repository import VehicleRepository
from app.services.exceptions import VehicleNotFoundError


def require_vehicle(repository: VehicleRepository, vehicle_id: str) -> Vehicle:
    """Return the vehicle with this id, or raise VehicleNotFoundError."""
    vehicle = repository.get(vehicle_id)
    if vehicle is None:
        raise VehicleNotFoundError()
    return vehicle
