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

# Two entries are deliberately out of stock so the dashboard always has a
# disabled Purchase button to show.
FLEET = [
    {"make": "Toyota", "model": "Corolla", "category": "Sedan", "price": 18500.0, "quantity": 6},
    {"make": "Toyota", "model": "RAV4", "category": "SUV", "price": 32000.0, "quantity": 3},
    {"make": "Toyota", "model": "Hilux", "category": "Truck", "price": 38900.0, "quantity": 2},
    {"make": "Honda", "model": "Civic", "category": "Sedan", "price": 22000.0, "quantity": 5},
    {"make": "Honda", "model": "CR-V", "category": "SUV", "price": 29500.0, "quantity": 4},
    {"make": "Honda", "model": "Jazz", "category": "Hatchback", "price": 16250.0, "quantity": 7},
    {"make": "Ford", "model": "F-150", "category": "Truck", "price": 45000.0, "quantity": 0},
    {"make": "Ford", "model": "Mustang", "category": "Coupe", "price": 58000.0, "quantity": 1},
    {"make": "Hyundai", "model": "i20", "category": "Hatchback", "price": 14750.0, "quantity": 9},
    {"make": "Hyundai", "model": "Creta", "category": "SUV", "price": 24300.0, "quantity": 4},
    {"make": "Tata", "model": "Nexon EV", "category": "Electric", "price": 21500.0, "quantity": 3},
    {"make": "Mahindra", "model": "Thar", "category": "SUV", "price": 27800.0, "quantity": 0},
    {"make": "Maruti", "model": "Swift", "category": "Hatchback", "price": 12400.0, "quantity": 11},
    {"make": "Volkswagen", "model": "Polo", "category": "Hatchback", "price": 17900.0, "quantity": 5},
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

        service.create(**entry)
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
