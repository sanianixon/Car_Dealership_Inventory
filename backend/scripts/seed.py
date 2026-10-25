"""Populate the database with an administrator and a starter catalogue.

Run from the backend directory:

    python scripts/seed.py

Safe to run repeatedly: existing rows are left alone, so re-running after a
code change tops up what is missing instead of duplicating the fleet.

This script drives the same VehicleService the API uses. That is the payoff for
keeping the service layer free of request and response types: the business
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

ADMIN_EMAIL = "admin@dealership.com"
ADMIN_PASSWORD = "Admin#12345"


def _days_ago(days: int) -> date:
    """A date relative to today, so seeded records never look stale."""
    return date.today() - timedelta(days=days)


def _car(year: int, colour: str, price: float, owners: int, days: int) -> dict:
    """One car on the lot."""
    return {
        "year": year,
        "colour": colour,
        "price": price,
        "ownership_number": owners,
        "acquired_on": _days_ago(days),
    }


# Prices are rupees, at roughly what each model fetches used on an Indian
# forecourt. Each listing holds real cars that differ in year, colour, owner
# and price — which is the point: four Citys are four different cars.
#
# "sold" marks cars the dealership has already sold. They stay on the record
# and keep their listing visible with a disabled Purchase button, which is what
# a sold-out model should look like.
FLEET = [
    {
        "make": "Maruti", "model": "Swift", "category": "Hatchback",
        "units": [
            _car(2021, "Pearl White", 620000.0, 2, 42),
            _car(2022, "Fire Red", 690000.0, 1, 23),
            _car(2022, "Granite Grey", 705000.0, 1, 12),
            _car(2019, "Lucent Orange", 480000.0, 3, 96),
        ],
    },
    {
        "make": "Maruti", "model": "Baleno", "category": "Hatchback",
        "units": [
            _car(2022, "Nexa Blue", 780000.0, 1, 18),
            _car(2021, "Opulent Red", 710000.0, 2, 57),
        ],
    },
    {
        "make": "Hyundai", "model": "i20", "category": "Hatchback",
        "units": [
            _car(2022, "Polar White", 820000.0, 1, 63),
            _car(2020, "Titan Grey", 640000.0, 2, 110),
        ],
    },
    {
        "make": "Hyundai", "model": "Creta", "category": "SUV",
        "units": [
            _car(2023, "Abyss Black", 1890000.0, 1, 9),
            _car(2021, "Ranger Khaki", 1520000.0, 2, 71),
            _car(2022, "Polar White", 1680000.0, 1, 34),
        ],
    },
    {
        "make": "Tata", "model": "Nexon EV", "category": "Electric",
        "units": [
            _car(2023, "Pristine White", 1420000.0, 1, 27),
            _car(2022, "Daytona Grey", 1265000.0, 1, 49),
        ],
    },
    {
        "make": "Tata", "model": "Punch", "category": "SUV",
        "units": [_car(2022, "Atomic Orange", 740000.0, 2, 88)],
    },
    {
        "make": "Mahindra", "model": "Thar", "category": "SUV",
        "units": [
            {**_car(2022, "Red Rage", 1560000.0, 1, 120), "sold": True},
            {**_car(2021, "Napoli Black", 1385000.0, 2, 150), "sold": True},
        ],
    },
    {
        "make": "Mahindra", "model": "XUV700", "category": "SUV",
        "units": [
            _car(2023, "Electric Blue", 2190000.0, 1, 15),
            _car(2023, "Midnight Black", 2240000.0, 1, 6),
        ],
    },
    {
        "make": "Toyota", "model": "Innova Crysta", "category": "MPV",
        "units": [
            _car(2021, "Super White", 2080000.0, 2, 75),
            _car(2022, "Attitude Black", 2320000.0, 1, 30),
        ],
    },
    {
        "make": "Toyota", "model": "Fortuner", "category": "SUV",
        "units": [_car(2022, "Phantom Brown", 3850000.0, 1, 33)],
    },
    {
        "make": "Honda", "model": "City", "category": "Sedan",
        "units": [
            _car(2022, "Platinum White", 1180000.0, 1, 21),
            _car(2020, "Radiant Red", 915000.0, 3, 134),
            _car(2023, "Meteoroid Grey", 1345000.0, 1, 8),
        ],
    },
    {
        "make": "Honda", "model": "Amaze", "category": "Sedan",
        "units": [_car(2021, "Golden Brown", 690000.0, 3, 140)],
    },
    {
        "make": "Kia", "model": "Seltos", "category": "SUV",
        "units": [
            _car(2023, "Gravity Grey", 1690000.0, 1, 11),
            _car(2022, "Intense Red", 1545000.0, 1, 45),
        ],
    },
    {
        "make": "Skoda", "model": "Slavia", "category": "Sedan",
        "units": [{**_car(2023, "Crystal Blue", 1320000.0, 1, 54), "sold": True}],
    },
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


def seed_fleet(session) -> tuple[int, int]:
    """Add any missing listings with their cars.

    Returns (listings added, cars added).
    """
    repository = VehicleRepository(session)
    service = VehicleService(repository)
    listings = cars = 0

    for entry in FLEET:
        if repository.find_by_model(entry["make"], entry["model"]) is not None:
            continue

        units = [{key: value for key, value in unit.items() if key != "sold"}
                 for unit in entry["units"]]
        vehicle = service.create(
            make=entry["make"],
            model=entry["model"],
            category=entry["category"],
            units=units,
        )
        listings += 1
        cars += len(units)

        # Cars marked sold are claimed through the same guarded update the API
        # uses, so the seeded history is produced the same way a real sale is.
        for unit, spec in zip(vehicle.units, entry["units"]):
            if spec.get("sold"):
                repository.claim_unit(unit.id)

    return listings, cars


def main() -> None:
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as session:
        admin_created = seed_admin(session)
        listings_added, cars_added = seed_fleet(session)
        catalogue = list(session.scalars(select(Vehicle)))
        in_stock = sum(vehicle.quantity for vehicle in catalogue)
        sold_out = [v.model for v in catalogue if v.quantity == 0]

    print(f"admin {ADMIN_EMAIL}: {'created' if admin_created else 'already present'}")
    print(f"listings added: {listings_added}, cars added: {cars_added}")
    print(f"catalogue: {len(catalogue)} models, {in_stock} cars available")
    print(f"sold out: {', '.join(sold_out) if sold_out else 'none'}")
    if admin_created:
        print(f"admin password: {ADMIN_PASSWORD}")


if __name__ == "__main__":
    main()
