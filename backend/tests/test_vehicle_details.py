"""Tests for the individual cars behind a listing.

Build year, colour, ownership and acquisition date describe one car, not a
model. These cover that they are stored per car, and that a listing's price,
stock and colours are derived from its cars rather than stored alongside them.
"""

from datetime import date, timedelta

ACQUIRED = (date.today() - timedelta(days=30)).isoformat()

UNIT = {
    "year": 2022,
    "colour": "Pearl White",
    "price": 1180000.0,
    "ownershipNumber": 1,
    "acquiredOn": ACQUIRED,
}

LISTING = {"make": "Honda", "model": "City", "category": "Sedan", "units": [UNIT]}


def _admin(auth):
    return auth(email="boss@dealership.com", admin=True)


def test_each_car_keeps_its_own_history(client, auth):
    """The point of the whole two-level model.

    Four Citys on a forecourt are four different cars: different years,
    colours, owners and prices. Before this they shared one row and therefore
    one history, which was nonsense.
    """
    res = client.post(
        "/api/vehicles",
        json={
            **LISTING,
            "units": [
                {**UNIT, "year": 2021, "colour": "Golden Brown", "ownershipNumber": 3,
                 "price": 980000.0},
                {**UNIT, "year": 2023, "colour": "Radiant Red", "ownershipNumber": 1,
                 "price": 1340000.0},
            ],
        },
        headers=_admin(auth),
    )
    assert res.status_code == 201

    detail = client.get(
        f"/api/vehicles/{res.json()['vehicle']['id']}", headers=auth()
    ).json()["vehicle"]

    by_year = {unit["year"]: unit for unit in detail["units"]}
    assert by_year[2021]["colour"] == "Golden Brown"
    assert by_year[2021]["ownershipNumber"] == 3
    assert by_year[2021]["price"] == 980000.0
    assert by_year[2023]["colour"] == "Radiant Red"
    assert by_year[2023]["ownershipNumber"] == 1


def test_the_listing_price_follows_the_cheapest_available_car(client, auth, add_vehicle):
    vehicle = add_vehicle(units=[{"price": 1340000.0}, {"price": 980000.0}])

    listed = client.get("/api/vehicles", headers=auth()).json()["vehicles"][0]

    assert listed["price"] == 980000.0
    assert vehicle["price"] == 980000.0


def test_colours_are_the_distinct_colours_actually_in_stock(client, auth, add_vehicle):
    add_vehicle(
        units=[{"colour": "Radiant Red"}, {"colour": "Pearl White"}, {"colour": "Radiant Red"}]
    )

    listed = client.get("/api/vehicles", headers=auth()).json()["vehicles"][0]

    # Three cars, two colours, listed once each and in order.
    assert listed["colours"] == ["Pearl White", "Radiant Red"]


def test_a_sold_car_stops_counting_towards_the_listing(client, auth, add_vehicle):
    vehicle = add_vehicle(units=[{"price": 980000.0}, {"price": 1340000.0}])
    cheapest = vehicle["unitIds"][0]

    client.post(
        f"/api/vehicles/{vehicle['id']}/purchase",
        json={"unitId": cheapest},
        headers=auth(),
    )

    listed = client.get("/api/vehicles", headers=auth()).json()["vehicles"][0]
    assert listed["quantity"] == 1
    # The advertised price rises, because the cheap one has gone.
    assert listed["price"] == 1340000.0


def test_year_must_be_plausible(client, auth):
    headers = _admin(auth)

    too_old = client.post(
        "/api/vehicles", json={**LISTING, "units": [{**UNIT, "year": 1799}]}, headers=headers
    )
    too_new = client.post(
        "/api/vehicles",
        json={**LISTING, "units": [{**UNIT, "year": date.today().year + 5}]},
        headers=headers,
    )

    assert too_old.status_code == 400
    assert too_new.status_code == 400


def test_next_year_is_allowed_because_new_models_arrive_early(client, auth):
    res = client.post(
        "/api/vehicles",
        json={**LISTING, "units": [{**UNIT, "year": date.today().year + 1}]},
        headers=_admin(auth),
    )

    assert res.status_code == 201


def test_ownership_number_starts_at_one(client, auth):
    headers = _admin(auth)

    for invalid in (0, -1):
        res = client.post(
            "/api/vehicles",
            json={**LISTING, "units": [{**UNIT, "ownershipNumber": invalid}]},
            headers=headers,
        )
        assert res.status_code == 400


def test_ownership_defaults_to_the_first_owner(client, auth):
    unit = {key: value for key, value in UNIT.items() if key != "ownershipNumber"}

    res = client.post(
        "/api/vehicles", json={**LISTING, "units": [unit]}, headers=_admin(auth)
    )

    assert res.status_code == 201
    detail = client.get(
        f"/api/vehicles/{res.json()['vehicle']['id']}", headers=auth()
    ).json()["vehicle"]
    assert detail["units"][0]["ownershipNumber"] == 1


def test_a_car_cannot_have_arrived_in_the_future(client, auth):
    tomorrow = (date.today() + timedelta(days=1)).isoformat()

    res = client.post(
        "/api/vehicles",
        json={**LISTING, "units": [{**UNIT, "acquiredOn": tomorrow}]},
        headers=_admin(auth),
    )

    assert res.status_code == 400


def test_today_is_a_valid_acquisition_date(client, auth):
    res = client.post(
        "/api/vehicles",
        json={**LISTING, "units": [{**UNIT, "acquiredOn": date.today().isoformat()}]},
        headers=_admin(auth),
    )

    assert res.status_code == 201


def test_a_blank_colour_is_rejected(client, auth):
    res = client.post(
        "/api/vehicles",
        json={**LISTING, "units": [{**UNIT, "colour": "   "}]},
        headers=_admin(auth),
    )

    assert res.status_code == 400


def test_a_price_sent_as_a_string_is_rejected(client, auth):
    """Pydantic would coerce "1180000" happily; silently accepting a string
    hides a bug in the caller, so the API contract insists on a JSON number."""
    res = client.post(
        "/api/vehicles",
        json={**LISTING, "units": [{**UNIT, "price": "1180000"}]},
        headers=_admin(auth),
    )

    assert res.status_code == 400


def test_a_year_sent_as_a_string_is_rejected(client, auth):
    res = client.post(
        "/api/vehicles",
        json={**LISTING, "units": [{**UNIT, "year": "2022"}]},
        headers=_admin(auth),
    )

    assert res.status_code == 400
