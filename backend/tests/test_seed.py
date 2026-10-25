"""Tests for the seed script.

Seeding was previously checked in CI by running the script twice and grepping
its output for a phrase. That broke the moment the script's wording changed,
while the script itself was fine — the check was asserting on a print
statement. These assert on the behaviour instead, where the suite can keep
them honest.
"""

from scripts.seed import seed_admin, seed_fleet


def test_seeding_an_empty_database_creates_the_catalogue(db):
    created = seed_admin(db)
    listings, cars = seed_fleet(db)

    assert created is True
    assert listings > 0
    # Every listing has at least one car, so there are never fewer cars than
    # listings. The whole point of the two-level model is that cars outnumber
    # them.
    assert cars > listings


def test_seeding_twice_changes_nothing(db):
    seed_admin(db)
    seed_fleet(db)

    assert seed_admin(db) is False
    assert seed_fleet(db) == (0, 0)


def test_the_seeded_fleet_has_sold_out_models(db):
    """The dashboard needs one, or the disabled Purchase button never shows."""
    from sqlalchemy import select

    from app.models import Vehicle

    seed_fleet(db)

    catalogue = list(db.scalars(select(Vehicle)))
    assert any(vehicle.quantity == 0 for vehicle in catalogue)
    assert any(vehicle.quantity > 0 for vehicle in catalogue)


def test_seeded_cars_of_one_model_genuinely_differ(db):
    """The bug that prompted the remodel: four identical cars.

    At least one seeded model must hold cars that differ in year, colour and
    price, or the catalogue is back to pretending a model is a car.
    """
    from sqlalchemy import select

    from app.models import Vehicle

    seed_fleet(db)

    varied = [
        vehicle
        for vehicle in db.scalars(select(Vehicle))
        if len({unit.year for unit in vehicle.units}) > 1
        and len({unit.colour for unit in vehicle.units}) > 1
        and len({unit.price for unit in vehicle.units}) > 1
    ]
    assert varied, "no seeded model has cars that differ from one another"
