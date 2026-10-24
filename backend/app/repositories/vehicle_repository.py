"""Data access for vehicles.

Every vehicle query lives here, so the service layer never builds SQL and the
routes never touch a Session. Swapping the storage engine means rewriting this
class and nothing above it.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Vehicle


class VehicleRepository:
    """SQLAlchemy-backed collection of vehicles."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def add(self, vehicle: Vehicle) -> Vehicle:
        """Persist a new vehicle and return it with its generated columns."""
        self._db.add(vehicle)
        self._db.commit()
        self._db.refresh(vehicle)
        return vehicle

    def list_all(self) -> list[Vehicle]:
        """Return every vehicle, in stock or not, ordered for display."""
        statement = select(Vehicle).order_by(Vehicle.make, Vehicle.model)
        return list(self._db.scalars(statement))

    def get(self, vehicle_id: str) -> Vehicle | None:
        """Return one vehicle, or None if the id is unknown."""
        return self._db.get(Vehicle, vehicle_id)

    def save(self, vehicle: Vehicle) -> Vehicle:
        """Flush pending changes to an already-tracked vehicle."""
        self._db.commit()
        self._db.refresh(vehicle)
        return vehicle

    def delete(self, vehicle: Vehicle) -> None:
        """Remove a vehicle from the catalogue."""
        self._db.delete(vehicle)
        self._db.commit()
