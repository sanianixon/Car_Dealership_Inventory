"""SQLAlchemy ORM models.

The catalogue is two levels, because a dealership's stock is two levels.

A `Vehicle` is a *listing*: Honda City, a sedan. It has no year, colour, price
or stock count of its own, because those belong to individual cars.

A `VehicleUnit` is *one car on the lot*: this Honda City, built 2022, white,
second owner, taken in on 14 March, priced at 11.8 lakh. It is sold once and
then it is gone.

An earlier version put year, colour and ownership on the listing itself, which
produced four identical Honda Citys all built in the same year by the same
owner. Stock counts and prices are therefore derived from the units rather than
stored, so the two can never disagree.
"""

import uuid
from datetime import date, datetime, timezone

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _new_id() -> str:
    """Generate a unique, non-sequential primary key."""
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    """An account that can sign in and buy vehicles."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(16), nullable=False, default="user")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utcnow)


class Vehicle(Base):
    """A model the dealership lists, such as "Honda City".

    Carries nothing that varies between individual cars. Its price and stock
    count are computed from its units.
    """

    __tablename__ = "vehicles"

    # One listing per model. Two "Honda City" rows would split the same cars
    # across two cards on the dashboard.
    __table_args__ = (UniqueConstraint("make", "model", name="uq_vehicles_make_model"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    make: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    model: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=_utcnow, onupdate=_utcnow
    )

    units: Mapped[list["VehicleUnit"]] = relationship(
        back_populates="vehicle",
        # Deleting a listing takes its cars with it: a unit without a listing
        # has no meaning, and the database should not need the service layer's
        # help to know that.
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    @property
    def available_units(self) -> list["VehicleUnit"]:
        """The cars still for sale, cheapest first."""
        return sorted(
            (unit for unit in self.units if unit.sold_at is None),
            key=lambda unit: unit.price,
        )

    @property
    def quantity(self) -> int:
        """How many of this model are on the lot. Derived, never stored."""
        return len(self.available_units)

    @property
    def price(self) -> float:
        """The lowest price among available cars, which is what a listing shows.

        Zero when nothing is available: the card is sold out, and the figure is
        struck through rather than read.
        """
        available = self.available_units
        return available[0].price if available else 0.0

    @property
    def colours(self) -> list[str]:
        """The distinct colours actually on the lot, in alphabetical order."""
        return sorted({unit.colour for unit in self.available_units})


class VehicleUnit(Base):
    """One physical car, with its own history and its own price."""

    __tablename__ = "vehicle_units"

    __table_args__ = (
        CheckConstraint("price >= 0", name="ck_units_price_non_negative"),
        CheckConstraint("year >= 1900", name="ck_units_year_plausible"),
        CheckConstraint("ownership_number >= 1", name="ck_units_ownership_positive"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    vehicle_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False, index=True
    )

    year: Mapped[int] = mapped_column(Integer, nullable=False)
    # One car is one colour. The listing reports the set of colours available.
    colour: Mapped[str] = mapped_column(String(40), nullable=False)
    # 1 means first owner, as used-car listings count it.
    ownership_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    # The day the dealership took this car in.
    acquired_on: Mapped[date] = mapped_column(Date, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)

    # Null while the car is for sale. Set once, when it sells, which is what
    # makes a unit claimable exactly once.
    sold_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, default=None)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=_utcnow, onupdate=_utcnow
    )

    vehicle: Mapped[Vehicle] = relationship(back_populates="units")

    @property
    def is_available(self) -> bool:
        return self.sold_at is None
