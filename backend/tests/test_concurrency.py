"""Tests that a car cannot be sold twice when buyers genuinely overlap.

These exercise the service layer directly, each buyer with its own session on
one shared SQLite file, released simultaneously by a barrier. That is
deliberate: the HTTP tests use TestClient, which serialises requests through a
single blocking portal and so cannot create contention at all.

These are the tests that distinguish a guarded UPDATE from a
read-check-then-write. Against the naive version the first sells one car ten
times over; against the guarded UPDATE exactly one buyer wins.
"""

import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta

from sqlalchemy.orm import sessionmaker

from app.models import Vehicle, VehicleUnit
from app.repositories.vehicle_repository import VehicleRepository
from app.services.exceptions import DomainError
from app.services.inventory_service import InventoryService


def _listing_with(factory: sessionmaker, cars: int) -> tuple[str, list[str]]:
    """Create a listing holding `cars` available cars."""
    session = factory()
    vehicle = Vehicle(
        make="Honda",
        model="City",
        category="Sedan",
        units=[
            VehicleUnit(
                year=2022,
                colour="Pearl White",
                ownership_number=1,
                acquired_on=date.today() - timedelta(days=30),
                price=1180000.0 + index,
            )
            for index in range(cars)
        ],
    )
    session.add(vehicle)
    session.commit()
    session.refresh(vehicle)
    ids = (vehicle.id, [unit.id for unit in vehicle.units])
    session.close()
    return ids


def _available(factory: sessionmaker, vehicle_id: str) -> int:
    session = factory()
    try:
        return session.get(Vehicle, vehicle_id).quantity
    finally:
        session.close()


def _buy_together(
    factory: sessionmaker, vehicle_id: str, buyers: int, unit_id: str | None
) -> list[str]:
    """Have `buyers` threads each try to buy at the same moment.

    Each thread reads the listing, then waits on the barrier, so every buyer
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
            service.purchase(vehicle_id, unit_id)
            return "sold"
        except DomainError:
            return "refused"
        finally:
            session.close()

    with ThreadPoolExecutor(max_workers=buyers) as pool:
        return [future.result() for future in [pool.submit(buy) for _ in range(buyers)]]


def test_two_buyers_cannot_both_take_the_same_car(temp_db):
    """The decisive case: ten buyers all name the same car."""
    vehicle_id, unit_ids = _listing_with(temp_db, cars=1)

    outcomes = _buy_together(temp_db, vehicle_id, buyers=10, unit_id=unit_ids[0])

    assert outcomes.count("sold") == 1
    assert outcomes.count("refused") == 9
    assert _available(temp_db, vehicle_id) == 0


def test_simultaneous_buyers_cannot_oversell_the_last_car(temp_db):
    """Ten buyers ask for "a City" when only one City remains."""
    vehicle_id, _ = _listing_with(temp_db, cars=1)

    outcomes = _buy_together(temp_db, vehicle_id, buyers=10, unit_id=None)

    assert outcomes.count("sold") == 1
    assert _available(temp_db, vehicle_id) == 0


def test_simultaneous_buyers_sell_exactly_the_cars_available(temp_db):
    """With three cars and ten buyers, exactly three may be sold."""
    vehicle_id, _ = _listing_with(temp_db, cars=3)

    outcomes = _buy_together(temp_db, vehicle_id, buyers=10, unit_id=None)

    assert outcomes.count("sold") == 3
    assert outcomes.count("refused") == 7
    assert _available(temp_db, vehicle_id) == 0
