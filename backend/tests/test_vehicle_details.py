"""Tests for the provenance fields a buyer wants before committing.

A price and a stock count are not enough to choose a used car. These cover the
build year, the colours on the lot, how many owners the car has had, and when
the dealership took it in.
"""

from datetime import date, timedelta

DETAILED = {
    "make": "Maruti",
    "model": "Swift",
    "category": "Hatchback",
    "price": 650000.0,
    "quantity": 4,
    "year": 2021,
    "colours": ["Pearl White", "Fire Red"],
    "ownershipNumber": 1,
    "acquiredOn": "2026-03-14",
}


def _admin(auth):
    return auth(email="boss@dealership.com", admin=True)


def test_create_stores_and_returns_the_detail_fields(client, auth):
    res = client.post("/api/vehicles", json=DETAILED, headers=_admin(auth))

    assert res.status_code == 201
    vehicle = res.json()["vehicle"]
    assert vehicle["year"] == 2021
    assert vehicle["colours"] == ["Pearl White", "Fire Red"]
    assert vehicle["ownershipNumber"] == 1
    assert vehicle["acquiredOn"] == "2026-03-14"


def test_details_survive_a_round_trip_through_the_list(client, auth):
    client.post("/api/vehicles", json=DETAILED, headers=_admin(auth))

    listed = client.get("/api/vehicles", headers=auth()).json()["vehicles"][0]

    assert listed["colours"] == ["Pearl White", "Fire Red"]
    assert listed["year"] == 2021


def test_a_single_colour_is_accepted(client, auth):
    res = client.post(
        "/api/vehicles",
        json={**DETAILED, "colours": ["Midnight Blue"]},
        headers=_admin(auth),
    )

    assert res.status_code == 201
    assert res.json()["vehicle"]["colours"] == ["Midnight Blue"]


def test_colours_cannot_be_empty(client, auth):
    """A vehicle on the forecourt is some colour; an empty list is a mistake."""
    res = client.post(
        "/api/vehicles", json={**DETAILED, "colours": []}, headers=_admin(auth)
    )

    assert res.status_code == 400
    assert "colours" in [d["path"] for d in res.json()["error"]["details"]]


def test_blank_colour_names_are_rejected(client, auth):
    res = client.post(
        "/api/vehicles",
        json={**DETAILED, "colours": ["Pearl White", "   "]},
        headers=_admin(auth),
    )

    assert res.status_code == 400


def test_duplicate_colours_are_collapsed(client, auth):
    """Listing the same colour twice is noise, not information."""
    res = client.post(
        "/api/vehicles",
        json={**DETAILED, "colours": ["Red", "red", " Red "]},
        headers=_admin(auth),
    )

    assert res.status_code == 201
    assert res.json()["vehicle"]["colours"] == ["Red"]


def test_year_must_be_plausible(client, auth):
    headers = _admin(auth)

    too_old = client.post("/api/vehicles", json={**DETAILED, "year": 1799}, headers=headers)
    too_new = client.post(
        "/api/vehicles", json={**DETAILED, "year": date.today().year + 5}, headers=headers
    )

    assert too_old.status_code == 400
    assert too_new.status_code == 400


def test_next_year_is_allowed_because_new_models_arrive_early(client, auth):
    res = client.post(
        "/api/vehicles",
        json={**DETAILED, "year": date.today().year + 1},
        headers=_admin(auth),
    )

    assert res.status_code == 201


def test_ownership_number_starts_at_one(client, auth):
    headers = _admin(auth)

    assert (
        client.post(
            "/api/vehicles", json={**DETAILED, "ownershipNumber": 0}, headers=headers
        ).status_code
        == 400
    )
    assert (
        client.post(
            "/api/vehicles", json={**DETAILED, "ownershipNumber": -1}, headers=headers
        ).status_code
        == 400
    )


def test_a_vehicle_cannot_have_arrived_in_the_future(client, auth):
    tomorrow = (date.today() + timedelta(days=1)).isoformat()

    res = client.post(
        "/api/vehicles", json={**DETAILED, "acquiredOn": tomorrow}, headers=_admin(auth)
    )

    assert res.status_code == 400
    assert "acquiredOn" in [d["path"] for d in res.json()["error"]["details"]]


def test_today_is_a_valid_acquisition_date(client, auth):
    res = client.post(
        "/api/vehicles",
        json={**DETAILED, "acquiredOn": date.today().isoformat()},
        headers=_admin(auth),
    )

    assert res.status_code == 201


def test_colours_can_be_updated(client, auth):
    headers = _admin(auth)
    created = client.post("/api/vehicles", json=DETAILED, headers=headers).json()["vehicle"]

    res = client.put(
        f"/api/vehicles/{created['id']}",
        json={"colours": ["Granite Grey"]},
        headers=headers,
    )

    assert res.status_code == 200
    assert res.json()["vehicle"]["colours"] == ["Granite Grey"]
    # The fields not mentioned must be untouched.
    assert res.json()["vehicle"]["year"] == 2021
