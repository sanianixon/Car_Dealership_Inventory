"""Data access for listings and the individual cars behind them.

Every vehicle query lives here, so the service layer never builds SQL and the
routes never touch a Session. Swapping the storage engine means rewriting this
class and nothing above it.
"""

from datetime import datetime, timezone

from sqlalchemy import Select, exists, select, update
from sqlalchemy.orm import Session, selectinload

from app.models import Vehicle, VehicleUnit

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
    """SQLAlchemy-backed collection of listings and units."""

    def __init__(self, db: Session) -> None:
        self._db = db

    # Units are loaded with their listing in one extra query rather than one
    # per listing, since every caller reads the derived price and stock count.
    def _with_units(self, statement: Select) -> Select:
        return statement.options(selectinload(Vehicle.units))

    def add(self, vehicle: Vehicle) -> Vehicle:
        """Persist a new listing and its units."""
        self._db.add(vehicle)
        self._db.commit()
        self._db.refresh(vehicle)
        return vehicle

    def list_all(self) -> list[Vehicle]:
        """Every listing, in stock or not, ordered for display."""
        statement = self._with_units(select(Vehicle).order_by(Vehicle.make, Vehicle.model))
        return list(self._db.scalars(statement))

    def get(self, vehicle_id: str) -> Vehicle | None:
        """Return one listing with its units, or None if the id is unknown."""
        statement = self._with_units(select(Vehicle).where(Vehicle.id == vehicle_id))
        return self._db.scalar(statement)

    def find_by_model(self, make: str, model: str) -> Vehicle | None:
        """Look a listing up by the pair that identifies it."""
        statement = self._with_units(
            select(Vehicle).where(Vehicle.make == make, Vehicle.model == model)
        )
        return self._db.scalar(statement)

    def save(self, vehicle: Vehicle) -> Vehicle:
        """Flush pending changes to an already-tracked listing."""
        self._db.commit()
        self._db.refresh(vehicle)
        return vehicle

    def delete(self, vehicle: Vehicle) -> None:
        """Remove a listing, and with it the cars it holds."""
        self._db.delete(vehicle)
        self._db.commit()

    def add_units(self, vehicle: Vehicle, units: list[VehicleUnit]) -> list[VehicleUnit]:
        """Take more cars of this model onto the lot."""
        for unit in units:
            unit.vehicle_id = vehicle.id
            self._db.add(unit)
        self._db.commit()
        for unit in units:
            self._db.refresh(unit)
        return units

    def claim_unit(self, unit_id: str) -> int:
        """Mark one car sold, but only if it is still for sale.

        The check and the write are one statement, so two buyers cannot both
        find the car available and then both take it. The caller inspects the
        number of rows affected: 0 means the guard refused, never that a car
        was sold twice.
        """
        statement = (
            update(VehicleUnit)
            .where(VehicleUnit.id == unit_id, VehicleUnit.sold_at.is_(None))
            .values(sold_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc))
        )
        rows = self._db.execute(statement).rowcount
        self._db.commit()
        return rows

    def search(
        self,
        *,
        make: str | None = None,
        model: str | None = None,
        category: str | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
    ) -> list[Vehicle]:
        """Return the listings matching every supplied filter.

        A price filter asks about the cars themselves, so it matches a listing
        that has at least one *available* car in range. A listing whose only
        car in that range has sold is therefore not a match, which is the
        answer a buyer wants.

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

        if min_price is not None or max_price is not None:
            in_range = [
                VehicleUnit.vehicle_id == Vehicle.id,
                VehicleUnit.sold_at.is_(None),
            ]
            if min_price is not None:
                in_range.append(VehicleUnit.price >= min_price)
            if max_price is not None:
                in_range.append(VehicleUnit.price <= max_price)
            statement = statement.where(exists().where(*in_range))

        statement = statement.order_by(Vehicle.make, Vehicle.model)
        return list(self._db.scalars(self._with_units(statement)))
