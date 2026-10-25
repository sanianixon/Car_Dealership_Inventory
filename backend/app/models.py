"""SQLAlchemy ORM models."""

import uuid
from datetime import date, datetime, timezone

from sqlalchemy import CheckConstraint, Date, DateTime, Float, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

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
    """A vehicle model held in inventory, with the number of units in stock."""

    __tablename__ = "vehicles"

    # Enforced by the database as well as by the request schemas. Validation
    # protects the API; these constraints protect the data from any other
    # writer, including the seed script and a future bug in the service layer.
    __table_args__ = (
        CheckConstraint("quantity >= 0", name="ck_vehicles_quantity_non_negative"),
        CheckConstraint("price >= 0", name="ck_vehicles_price_non_negative"),
        CheckConstraint("year >= 1900", name="ck_vehicles_year_plausible"),
        CheckConstraint(
            "ownership_number >= 1", name="ck_vehicles_ownership_number_positive"
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    make: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    model: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    year: Mapped[int] = mapped_column(Integer, nullable=False)

    # The colours this model is available in on the lot. Stored as a JSON list
    # rather than a child table: nothing queries or filters by colour, so a
    # join table would be structure without a purpose. Normalising is a
    # contained change if filtering by colour is ever wanted.
    colours: Mapped[list[str]] = mapped_column(JSON, nullable=False)

    # 1 means first owner, as used-car listings count it.
    ownership_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # The day the dealership took the vehicle in.
    acquired_on: Mapped[date] = mapped_column(Date, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=_utcnow, onupdate=_utcnow
    )
