"""Tests that stock cannot be oversold when buyers genuinely overlap.

These exercise the service layer directly, each buyer with its own session on
one shared SQLite file, released simultaneously by a barrier. That is
deliberate: the HTTP tests use TestClient, which serialises requests through a
single blocking portal and so cannot create contention at all.

These are the tests that distinguish a guarded UPDATE from a
read-check-then-write. Against the naive version the first sells ten units of
a single car; against the guarded UPDATE exactly one buyer wins.
"""

import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta

from sqlalchemy.orm import sessionmaker

from app.models import Vehicle
from app.repositories.vehicle_repository import VehicleRepository
from app.services.exceptions import DomainError
from app.services.inventory_service import InventoryService


def _vehicle_with_stock(factory: sessionmaker, quantity: int) -> str:
    """Create a vehicle holding `quantity` units and return its id."""
    session = factory()
    vehicle = Vehicle(
        make="Toyota",
        model="Corolla",
        category="Sedan",
        price=650000.0,
        quantity=quantity,
        year=2021,
        colours=["Pearl White"],
        ownership_number=1,
        acquired_on=date.today() - timedelta(days=30),
    )
    session.add(vehicle)
    session.commit()
    vehicle_id = vehicle.id
    session.close()
    return vehicle_id


def _quantity(factory: sessionmaker, vehicle_id: str) -> int:
    session = factory()
    try:
        return session.get(Vehicle, vehicle_id).quantity
    finally:
        session.close()


def _buy_together(factory: sessionmaker, vehicle_id: str, buyers: int) -> list[str]:
    """Have `buyers` threads each buy one unit at the same moment.

    Each thread reads the vehicle, then waits on the barrier, so every buyer
    has seen the stock before any of them is allowed to write. That is the
    window a read-then-write implementation leaves open.
    """
    ready = threading.Barrier(buyers)

    def buy() -> str:
        session = factory()
        service = InventoryService(VehicleRepository(session))
        try:
            session.get(Vehicle, vehicle_id)
            ready.wait(timeout=15)
            service.purchase(vehicle_id, 1)
            return "sold"
        except DomainError:
            return "refused"
        finally:
            session.close()

    with ThreadPoolExecutor(max_workers=buyers) as pool:
        return [future.result() for future in [pool.submit(buy) for _ in range(buyers)]]


def test_simultaneous_buyers_cannot_oversell_the_last_unit(temp_db):
    vehicle_id = _vehicle_with_stock(temp_db, 1)

    outcomes = _buy_together(temp_db, vehicle_id, buyers=10)

    assert outcomes.count("sold") == 1
    assert outcomes.count("refused") == 9
    assert _quantity(temp_db, vehicle_id) == 0


def test_simultaneous_buyers_sell_exactly_the_available_stock(temp_db):
    """With three units and ten buyers, exactly three cars may be sold."""
    vehicle_id = _vehicle_with_stock(temp_db, 3)

    outcomes = _buy_together(temp_db, vehicle_id, buyers=10)

    assert outcomes.count("sold") == 3
    assert outcomes.count("refused") == 7
    assert _quantity(temp_db, vehicle_id) == 0
