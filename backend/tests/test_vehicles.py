"""Tests for creating, listing, fetching, updating and deleting vehicles.

Managing the catalogue is staff work, so create, update and delete all require
an administrator. Tests that merely need a vehicle to exist use the add_vehicle
fixture, which writes the row directly: setting a fixture up through
POST /api/vehicles would make those tests depend on the permissions of an
endpoint they are not testing.
"""

VALID = {
    "make": "Toyota",
    "model": "Corolla",
    "category": "Sedan",
    "price": 18500.0,
    "quantity": 4,
}


def test_creating_a_vehicle_requires_authentication(client):
    assert client.post("/api/vehicles", json=VALID).status_code == 401


def test_listing_vehicles_requires_authentication(client):
    assert client.get("/api/vehicles").status_code == 401


def test_create_returns_the_stored_vehicle(client, auth):
    res = client.post("/api/vehicles", json=VALID, headers=auth(admin=True))

    assert res.status_code == 201
    vehicle = res.json()["vehicle"]
    assert vehicle["make"] == "Toyota"
    assert vehicle["price"] == 18500.0
    assert vehicle["quantity"] == 4
    assert vehicle["id"]
    assert vehicle["createdAt"]
    assert vehicle["updatedAt"]


def test_create_rejects_a_negative_price(client, auth):
    res = client.post(
        "/api/vehicles", json={**VALID, "price": -1}, headers=auth(admin=True)
    )

    assert res.status_code == 400
    assert "price" in [d["path"] for d in res.json()["error"]["details"]]


def test_create_rejects_a_price_sent_as_a_string(client, auth):
    res = client.post(
        "/api/vehicles", json={**VALID, "price": "18500"}, headers=auth(admin=True)
    )

    assert res.status_code == 400


def test_create_rejects_a_fractional_quantity(client, auth):
    res = client.post(
        "/api/vehicles", json={**VALID, "quantity": 1.5}, headers=auth(admin=True)
    )

    assert res.status_code == 400


def test_create_rejects_a_negative_quantity(client, auth):
    res = client.post(
        "/api/vehicles", json={**VALID, "quantity": -2}, headers=auth(admin=True)
    )

    assert res.status_code == 400


def test_create_rejects_blank_text_fields(client, auth):
    res = client.post(
        "/api/vehicles", json={**VALID, "make": "   "}, headers=auth(admin=True)
    )

    assert res.status_code == 400


def test_list_includes_sold_out_vehicles_sorted_by_make_then_model(
    client, auth, add_vehicle
):
    add_vehicle(make="Honda", model="Civic")
    add_vehicle(make="Toyota", model="Yaris")
    add_vehicle(make="Toyota", model="Camry", quantity=0)

    res = client.get("/api/vehicles", headers=auth())

    assert res.status_code == 200
    listed = [(v["make"], v["model"]) for v in res.json()["vehicles"]]
    # Sold-out vehicles are included: the dashboard needs them in order to
    # render a disabled Purchase button.
    assert listed == [("Honda", "Civic"), ("Toyota", "Camry"), ("Toyota", "Yaris")]


def test_get_one_vehicle_by_id(client, auth, add_vehicle):
    vehicle = add_vehicle()

    res = client.get(f"/api/vehicles/{vehicle['id']}", headers=auth())

    assert res.status_code == 200
    assert res.json()["vehicle"]["id"] == vehicle["id"]


def test_get_unknown_vehicle_is_404(client, auth):
    res = client.get("/api/vehicles/does-not-exist", headers=auth())

    assert res.status_code == 404
    assert res.json()["error"]["message"]


def test_update_changes_only_the_supplied_fields(client, auth, add_vehicle):
    vehicle = add_vehicle()

    res = client.put(
        f"/api/vehicles/{vehicle['id']}",
        json={"price": 17250.0},
        headers=auth(admin=True),
    )

    assert res.status_code == 200
    updated = res.json()["vehicle"]
    assert updated["price"] == 17250.0
    assert updated["make"] == vehicle["make"]
    assert updated["quantity"] == vehicle["quantity"]


def test_update_requires_at_least_one_field(client, auth, add_vehicle):
    vehicle = add_vehicle()

    res = client.put(
        f"/api/vehicles/{vehicle['id']}", json={}, headers=auth(admin=True)
    )

    assert res.status_code == 400


def test_update_ignores_an_id_in_the_body(client, auth, add_vehicle):
    vehicle = add_vehicle()

    res = client.put(
        f"/api/vehicles/{vehicle['id']}",
        json={"id": "hijacked", "category": "Hatchback"},
        headers=auth(admin=True),
    )

    assert res.status_code == 200
    assert res.json()["vehicle"]["id"] == vehicle["id"]
    assert res.json()["vehicle"]["category"] == "Hatchback"


def test_update_rejects_an_invalid_price(client, auth, add_vehicle):
    vehicle = add_vehicle()

    res = client.put(
        f"/api/vehicles/{vehicle['id']}", json={"price": -5}, headers=auth(admin=True)
    )

    assert res.status_code == 400


def test_update_unknown_vehicle_is_404(client, auth):
    res = client.put(
        "/api/vehicles/does-not-exist",
        json={"price": 100.0},
        headers=auth(admin=True),
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
    # The vehicle must survive a rejected deletion.
    assert client.get(f"/api/vehicles/{vehicle['id']}", headers=headers).status_code == 200


def test_delete_as_admin_removes_the_vehicle(client, auth, add_vehicle):
    member = auth()
    admin = auth(email="boss@dealership.com", admin=True)
    vehicle = add_vehicle()

    res = client.delete(f"/api/vehicles/{vehicle['id']}", headers=admin)

    assert res.status_code == 204
    assert res.content == b""
    assert client.get(f"/api/vehicles/{vehicle['id']}", headers=member).status_code == 404


def test_delete_unknown_vehicle_is_404_for_admin(client, auth):
    admin = auth(email="boss@dealership.com", admin=True)

    assert client.delete("/api/vehicles/nope", headers=admin).status_code == 404


def test_adding_a_vehicle_is_forbidden_for_a_non_admin(client, auth):
    """Managing the catalogue is staff work, whatever the UI chooses to show.

    A buyer must not be able to add stock to the dealership by calling the API
    directly. Hiding the button is presentation, not a permission.
    """
    res = client.post("/api/vehicles", json=VALID, headers=auth())

    assert res.status_code == 403


def test_editing_a_vehicle_is_forbidden_for_a_non_admin(client, auth, add_vehicle):
    buyer = auth()
    vehicle = add_vehicle()

    res = client.put(
        f"/api/vehicles/{vehicle['id']}", json={"price": 1.0}, headers=buyer
    )

    assert res.status_code == 403
    # The rejected edit must not have changed anything.
    unchanged = client.get(f"/api/vehicles/{vehicle['id']}", headers=buyer).json()
    assert unchanged["vehicle"]["price"] == VALID["price"]


def test_an_admin_may_add_and_edit(client, auth):
    admin = auth(email="boss@dealership.com", admin=True)

    created = client.post("/api/vehicles", json=VALID, headers=admin)
    assert created.status_code == 201

    updated = client.put(
        f"/api/vehicles/{created.json()['vehicle']['id']}",
        json={"price": 17000.0},
        headers=admin,
    )
    assert updated.status_code == 200
    assert updated.json()["vehicle"]["price"] == 17000.0
