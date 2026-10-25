"""Populate the database with an administrator and a starter inventory.

Run from the backend directory:

    python scripts/seed.py

Safe to run repeatedly: existing rows are left alone, so re-running after a
code change tops up what is missing instead of duplicating the fleet.

This script drives the same VehicleService the API uses. That is the payoff
for keeping the service layer free of request and response types: the business
rules are reachable from a plain Python process, with no HTTP involved.
"""

import os
import sys
from datetime import date, timedelta

# Allow "python scripts/seed.py" from the backend directory by putting the
# project root (the parent of this file's directory) on the import path.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select  # noqa: E402

from app.database import Base, SessionLocal, engine  # noqa: E402
from app.models import User, Vehicle  # noqa: E402
from app.repositories.vehicle_repository import VehicleRepository  # noqa: E402
from app.security import hash_password  # noqa: E402
from app.services.vehicle_service import VehicleService  # noqa: E402

def _days_ago(days: int) -> date:
    """A date relative to today, so seeded records never look stale."""
    return date.today() - timedelta(days=days)


ADMIN_EMAIL = "admin@dealership.com"
ADMIN_PASSWORD = "Admin#12345"

# Prices are rupees, at roughly what each model fetches used on an Indian
# forecourt. Two entries are deliberately out of stock so the dashboard always
# has a disabled Purchase button to show.
FLEET = [
    {"make": "Maruti", "model": "Swift", "category": "Hatchback", "price": 650000.0,
     "quantity": 11, "year": 2021, "colours": ["Pearl White", "Fire Red", "Granite Grey"],
     "ownership_number": 1, "acquired_on": _days_ago(42)},
    {"make": "Maruti", "model": "Baleno", "category": "Hatchback", "price": 780000.0,
     "quantity": 6, "year": 2022, "colours": ["Nexa Blue", "Opulent Red"],
     "ownership_number": 1, "acquired_on": _days_ago(18)},
    {"make": "Hyundai", "model": "i20", "category": "Hatchback", "price": 820000.0,
     "quantity": 9, "year": 2022, "colours": ["Polar White", "Titan Grey"],
     "ownership_number": 2, "acquired_on": _days_ago(63)},
    {"make": "Hyundai", "model": "Creta", "category": "SUV", "price": 1850000.0,
     "quantity": 4, "year": 2023, "colours": ["Abyss Black", "Ranger Khaki"],
     "ownership_number": 1, "acquired_on": _days_ago(9)},
    {"make": "Tata", "model": "Nexon EV", "category": "Electric", "price": 1420000.0,
     "quantity": 3, "year": 2023, "colours": ["Pristine White", "Daytona Grey"],
     "ownership_number": 1, "acquired_on": _days_ago(27)},
    {"make": "Tata", "model": "Punch", "category": "SUV", "price": 740000.0,
     "quantity": 7, "year": 2022, "colours": ["Atomic Orange", "Tropical Mist"],
     "ownership_number": 2, "acquired_on": _days_ago(88)},
    {"make": "Mahindra", "model": "Thar", "category": "SUV", "price": 1560000.0,
     "quantity": 0, "year": 2022, "colours": ["Red Rage", "Napoli Black"],
     "ownership_number": 1, "acquired_on": _days_ago(120)},
    {"make": "Mahindra", "model": "XUV700", "category": "SUV", "price": 2190000.0,
     "quantity": 2, "year": 2023, "colours": ["Electric Blue", "Midnight Black"],
     "ownership_number": 1, "acquired_on": _days_ago(15)},
    {"make": "Toyota", "model": "Innova Crysta", "category": "MPV", "price": 2250000.0,
     "quantity": 3, "year": 2021, "colours": ["Super White", "Attitude Black"],
     "ownership_number": 2, "acquired_on": _days_ago(75)},
    {"make": "Toyota", "model": "Fortuner", "category": "SUV", "price": 3850000.0,
     "quantity": 1, "year": 2022, "colours": ["Phantom Brown", "Super White"],
     "ownership_number": 1, "acquired_on": _days_ago(33)},
    {"make": "Honda", "model": "City", "category": "Sedan", "price": 1180000.0,
     "quantity": 5, "year": 2022, "colours": ["Platinum White", "Radiant Red"],
     "ownership_number": 1, "acquired_on": _days_ago(21)},
    {"make": "Honda", "model": "Amaze", "category": "Sedan", "price": 690000.0,
     "quantity": 4, "year": 2021, "colours": ["Golden Brown", "Meteoroid Grey"],
     "ownership_number": 3, "acquired_on": _days_ago(140)},
    {"make": "Kia", "model": "Seltos", "category": "SUV", "price": 1690000.0,
     "quantity": 4, "year": 2023, "colours": ["Gravity Grey", "Intense Red"],
     "ownership_number": 1, "acquired_on": _days_ago(11)},
    {"make": "Skoda", "model": "Slavia", "category": "Sedan", "price": 1320000.0,
     "quantity": 0, "year": 2023, "colours": ["Crystal Blue", "Candy White"],
     "ownership_number": 1, "acquired_on": _days_ago(54)},
]


def seed_admin(session) -> bool:
    """Create the administrator account if it is not already there.

    Returns True if a row was inserted. The role is set here rather than
    through the API, which is the second route to an admin account alongside
    the invite code.
    """
    if session.scalar(select(User).where(User.email == ADMIN_EMAIL)) is not None:
        return False

    session.add(
        User(
            email=ADMIN_EMAIL,
            password_hash=hash_password(ADMIN_PASSWORD),
            role="admin",
        )
    )
    session.commit()
    return True


def seed_fleet(session) -> int:
    """Add any missing vehicles, identified by make and model.

    Returns the number inserted.
    """
    service = VehicleService(VehicleRepository(session))
    added = 0

    for entry in FLEET:
        already_there = session.scalar(
            select(Vehicle).where(
                Vehicle.make == entry["make"], Vehicle.model == entry["model"]
            )
        )
        if already_there is not None:
            continue

        service.create(entry)
        added += 1

    return added


def main() -> None:
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as session:
        admin_created = seed_admin(session)
        vehicles_added = seed_fleet(session)
        fleet_size = len(list(session.scalars(select(Vehicle))))

    print(f"admin {ADMIN_EMAIL}: {'created' if admin_created else 'already present'}")
    print(f"vehicles added: {vehicles_added}")
    print(f"vehicles in catalogue: {fleet_size}")
    if admin_created:
        print(f"admin password: {ADMIN_PASSWORD}")


if __name__ == "__main__":
    main()
