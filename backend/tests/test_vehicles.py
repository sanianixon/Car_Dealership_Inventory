"""Tests for listing, fetching, creating, updating and deleting listings.

A listing is a model — "Honda City" — and the cars behind it are its units.
Managing the catalogue is staff work, so create, update and delete all require
an administrator. Tests that merely need stock to exist use the add_vehicle
fixture, which writes the rows directly.
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

VALID = {
    "make": "Honda",
    "model": "City",
    "category": "Sedan",
    "units": [UNIT],
}


def _admin(auth):
    return auth(email="boss@dealership.com", admin=True)


def test_creating_a_listing_requires_authentication(client):
    assert client.post("/api/vehicles", json=VALID).status_code == 401


def test_listing_vehicles_requires_authentication(client):
    assert client.get("/api/vehicles").status_code == 401


def test_create_returns_the_listing_with_derived_stock(client, auth):
    res = client.post(
        "/api/vehicles",
        json={**VALID, "units": [UNIT, {**UNIT, "price": 1250000.0, "colour": "Radiant Red"}]},
        headers=_admin(auth),
    )

    assert res.status_code == 201
    vehicle = res.json()["vehicle"]
    assert vehicle["make"] == "Honda"
    assert vehicle["quantity"] == 2
    # The advertised price is the cheapest car available, not an average.
    assert vehicle["price"] == 1180000.0
    assert vehicle["colours"] == ["Pearl White", "Radiant Red"]


def test_a_listing_needs_at_least_one_car(client, auth):
    """A model in stock with no cars would show as sold out the moment it existed."""
    res = client.post(
        "/api/vehicles", json={**VALID, "units": []}, headers=_admin(auth)
    )

    assert res.status_code == 400


def test_the_same_model_cannot_be_listed_twice(client, auth):
    headers = _admin(auth)
    assert client.post("/api/vehicles", json=VALID, headers=headers).status_code == 201

    res = client.post("/api/vehicles", json=VALID, headers=headers)

    assert res.status_code == 409


def test_create_rejects_a_negative_price_on_a_car(client, auth):
    res = client.post(
        "/api/vehicles",
        json={**VALID, "units": [{**UNIT, "price": -1}]},
        headers=_admin(auth),
    )

    assert res.status_code == 400


def test_create_rejects_blank_text_fields(client, auth):
    res = client.post(
        "/api/vehicles", json={**VALID, "make": "   "}, headers=_admin(auth)
    )

    assert res.status_code == 400


def test_list_includes_sold_out_models_sorted_by_make_then_model(
    client, auth, add_vehicle
):
    add_vehicle(make="Honda", model="City")
    add_vehicle(make="Toyota", model="Innova")
    add_vehicle(make="Toyota", model="Fortuner", units=0)

    res = client.get("/api/vehicles", headers=auth())

    assert res.status_code == 200
    listed = [(v["make"], v["model"]) for v in res.json()["vehicles"]]
    # Sold-out models are included: the dashboard needs them in order to
    # render a disabled Purchase button.
    assert listed == [("Honda", "City"), ("Toyota", "Fortuner"), ("Toyota", "Innova")]


def test_a_sold_out_listing_reports_no_stock_and_no_colours(client, auth, add_vehicle):
    add_vehicle(units=0)

    listed = client.get("/api/vehicles", headers=auth()).json()["vehicles"][0]

    assert listed["quantity"] == 0
    assert listed["colours"] == []


def test_get_one_listing_returns_its_cars(client, auth, add_vehicle):
    vehicle = add_vehicle(
        units=[{"price": 650000.0, "colour": "Fire Red"}, {"price": 700000.0}]
    )

    res = client.get(f"/api/vehicles/{vehicle['id']}", headers=auth())

    assert res.status_code == 200
    body = res.json()["vehicle"]
    assert body["id"] == vehicle["id"]
    assert len(body["units"]) == 2
    assert {unit["colour"] for unit in body["units"]} == {"Fire Red", "Pearl White"}
    assert all(unit["isAvailable"] for unit in body["units"])


def test_get_unknown_listing_is_404(client, auth):
    res = client.get("/api/vehicles/does-not-exist", headers=auth())

    assert res.status_code == 404
    assert res.json()["error"]["message"]


def test_update_changes_only_the_supplied_fields(client, auth, add_vehicle):
    vehicle = add_vehicle()

    res = client.put(
        f"/api/vehicles/{vehicle['id']}",
        json={"category": "Hatchback"},
        headers=_admin(auth),
    )

    assert res.status_code == 200
    updated = res.json()["vehicle"]
    assert updated["category"] == "Hatchback"
    assert updated["make"] == vehicle["make"]


def test_update_requires_at_least_one_field(client, auth, add_vehicle):
    vehicle = add_vehicle()

    res = client.put(
        f"/api/vehicles/{vehicle['id']}", json={}, headers=_admin(auth)
    )

    assert res.status_code == 400


def test_update_cannot_collide_with_another_listing(client, auth, add_vehicle):
    add_vehicle(make="Honda", model="City")
    other = add_vehicle(make="Honda", model="Amaze")

    res = client.put(
        f"/api/vehicles/{other['id']}", json={"model": "City"}, headers=_admin(auth)
    )

    assert res.status_code == 409


def test_update_unknown_listing_is_404(client, auth):
    res = client.put(
        "/api/vehicles/does-not-exist", json={"category": "SUV"}, headers=_admin(auth)
    )

    assert res.status_code == 404


def test_delete_requires_authentication(client, add_vehicle):
    vehicle = add_vehicle()

    assert client.delete(f"/api/vehicles/{vehicle['id']}").status_code == 401


def test_delete_is_forbidden_for_a_non_admin(client, auth, add_vehicle):
    headers = auth()
    vehicle = add_vehicle()

    res = client.delete(f"/api/vehicles/{vehicle['id']}", headers=headers)

    assert res.status_code == 403
    # The listing must survive a rejected deletion.
    assert client.get(f"/api/vehicles/{vehicle['id']}", headers=headers).status_code == 200


def test_delete_as_admin_removes_the_listing_and_its_cars(client, auth, add_vehicle):
    member = auth()
    vehicle = add_vehicle(units=3)

    res = client.delete(f"/api/vehicles/{vehicle['id']}", headers=_admin(auth))

    assert res.status_code == 204
    assert res.content == b""
    assert client.get(f"/api/vehicles/{vehicle['id']}", headers=member).status_code == 404


def test_delete_unknown_listing_is_404_for_admin(client, auth):
    assert client.delete("/api/vehicles/nope", headers=_admin(auth)).status_code == 404


def test_adding_a_listing_is_forbidden_for_a_non_admin(client, auth):
    """Managing the catalogue is staff work, whatever the UI chooses to show.

    A buyer must not be able to add stock to the dealership by calling the API
    directly. Hiding the button is presentation, not a permission.
    """
    res = client.post("/api/vehicles", json=VALID, headers=auth())

    assert res.status_code == 403


def test_editing_a_listing_is_forbidden_for_a_non_admin(client, auth, add_vehicle):
    buyer = auth()
    vehicle = add_vehicle()

    res = client.put(
        f"/api/vehicles/{vehicle['id']}", json={"category": "SUV"}, headers=buyer
    )

    assert res.status_code == 403
    unchanged = client.get(f"/api/vehicles/{vehicle['id']}", headers=buyer).json()
    assert unchanged["vehicle"]["category"] == vehicle["category"]


def test_an_admin_may_add_and_edit(client, auth):
    admin = _admin(auth)

    created = client.post("/api/vehicles", json=VALID, headers=admin)
    assert created.status_code == 201

    updated = client.put(
        f"/api/vehicles/{created.json()['vehicle']['id']}",
        json={"category": "Compact Sedan"},
        headers=admin,
    )
    assert updated.status_code == 200
    assert updated.json()["vehicle"]["category"] == "Compact Sedan"
