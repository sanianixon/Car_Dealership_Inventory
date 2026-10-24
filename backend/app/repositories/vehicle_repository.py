"""Data access for vehicles.

Every vehicle query lives here, so the service layer never builds SQL and the
routes never touch a Session. Swapping the storage engine means rewriting this
class and nothing above it.
"""

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models import Vehicle

# LIKE treats "%" and "_" as wildcards, so a user searching for "100%" would
# otherwise match every row. They are escaped with a backslash, declared to
# SQL via ESCAPE.
_LIKE_ESCAPE = "\\"


def _contains_pattern(value: str) -> str:
    """Build a LIKE pattern matching `value` anywhere, wildcards disarmed."""
    escaped = (
        value.replace(_LIKE_ESCAPE, _LIKE_ESCAPE * 2)
        .replace("%", f"{_LIKE_ESCAPE}%")
        .replace("_", f"{_LIKE_ESCAPE}_")
    )
    return f"%{escaped}%"


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

    def search(
        self,
        *,
        make: str | None = None,
        model: str | None = None,
        category: str | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
    ) -> list[Vehicle]:
        """Return the vehicles matching every supplied filter.

        Values are bound as query parameters, never interpolated into the SQL
        string, so no search term can alter the statement.
        """
        statement: Select = select(Vehicle)

        for column, value in (
            (Vehicle.make, make),
            (Vehicle.model, model),
            (Vehicle.category, category),
        ):
            if value:
                statement = statement.where(
                    column.ilike(_contains_pattern(value), escape=_LIKE_ESCAPE)
                )

        if min_price is not None:
            statement = statement.where(Vehicle.price >= min_price)
        if max_price is not None:
            statement = statement.where(Vehicle.price <= max_price)

        statement = statement.order_by(Vehicle.make, Vehicle.model)
        return list(self._db.scalars(statement))
