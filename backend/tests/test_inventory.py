"""Tests for buying a specific car and for taking more cars in."""

from datetime import date, timedelta

ACQUIRED = (date.today() - timedelta(days=30)).isoformat()

UNIT = {
    "year": 2022,
    "colour": "Pearl White",
    "price": 1180000.0,
    "ownershipNumber": 1,
    "acquiredOn": ACQUIRED,
}


def _admin(auth):
    return auth(email="boss@dealership.com", admin=True)


def test_purchase_requires_authentication(client, add_vehicle):
    vehicle = add_vehicle()

    assert client.post(f"/api/vehicles/{vehicle['id']}/purchase").status_code == 401


def test_purchase_without_naming_a_car_takes_the_cheapest(client, auth, add_vehicle):
    """What "buy a Honda City" means on a forecourt."""
    vehicle = add_vehicle(units=[{"price": 1340000.0}, {"price": 980000.0}])

    res = client.post(f"/api/vehicles/{vehicle['id']}/purchase", json={}, headers=auth())

    assert res.status_code == 200
    body = res.json()
    assert body["unit"]["price"] == 980000.0
    assert body["unit"]["isAvailable"] is False
    assert body["vehicle"]["quantity"] == 1


def test_a_buyer_can_name_the_car_they_want(client, auth, add_vehicle):
    vehicle = add_vehicle(
        units=[{"price": 980000.0, "colour": "Fire Red"}, {"price": 1340000.0, "colour": "Jet Black"}]
    )
    dearer = vehicle["units"][1]["id"]

    res = client.post(
        f"/api/vehicles/{vehicle['id']}/purchase", json={"unitId": dearer}, headers=auth()
    )

    assert res.status_code == 200
    assert res.json()["unit"]["colour"] == "Jet Black"
    # The cheap one is still there, so the listing still advertises its price.
    assert res.json()["vehicle"]["price"] == 980000.0


def test_the_same_car_cannot_be_bought_twice(client, auth, add_vehicle):
    vehicle = add_vehicle(units=2)
    first = vehicle["unitIds"][0]
    headers = auth()

    assert (
        client.post(
            f"/api/vehicles/{vehicle['id']}/purchase",
            json={"unitId": first},
            headers=headers,
        ).status_code
        == 200
    )

    again = client.post(
        f"/api/vehicles/{vehicle['id']}/purchase", json={"unitId": first}, headers=headers
    )

    assert again.status_code == 409
    assert again.json()["error"]["message"]


def test_buying_from_a_sold_out_listing_is_rejected(client, auth, add_vehicle):
    vehicle = add_vehicle(units=0)

    res = client.post(f"/api/vehicles/{vehicle['id']}/purchase", json={}, headers=auth())

    assert res.status_code == 409
    assert res.json()["error"]["message"] == "Vehicle is out of stock"


def test_a_car_belonging_to_another_listing_cannot_be_bought_here(
    client, auth, add_vehicle
):
    """The unit must belong to the listing in the path.

    Otherwise any car in the dealership could be bought through any listing's
    URL, which is a confusing audit trail at best.
    """
    city = add_vehicle(make="Honda", model="City")
    amaze = add_vehicle(make="Honda", model="Amaze")

    res = client.post(
        f"/api/vehicles/{city['id']}/purchase",
        json={"unitId": amaze["unitIds"][0]},
        headers=auth(),
    )

    assert res.status_code == 404


def test_purchase_of_an_unknown_listing_is_404(client, auth):
    res = client.post("/api/vehicles/nope/purchase", json={}, headers=auth())

    assert res.status_code == 404


def test_buying_every_car_empties_the_listing(client, auth, add_vehicle):
    vehicle = add_vehicle(units=3)
    headers = auth()

    for unit_id in vehicle["unitIds"]:
        res = client.post(
            f"/api/vehicles/{vehicle['id']}/purchase",
            json={"unitId": unit_id},
            headers=headers,
        )
        assert res.status_code == 200

    listed = client.get(f"/api/vehicles/{vehicle['id']}", headers=headers).json()["vehicle"]
    assert listed["quantity"] == 0
    assert listed["colours"] == []
    assert all(unit["isAvailable"] is False for unit in listed["units"])


def test_restock_requires_authentication(client, add_vehicle):
    vehicle = add_vehicle()

    res = client.post(f"/api/vehicles/{vehicle['id']}/restock", json={"units": [UNIT]})

    assert res.status_code == 401


def test_restock_is_forbidden_for_a_non_admin(client, auth, add_vehicle):
    vehicle = add_vehicle()

    res = client.post(
        f"/api/vehicles/{vehicle['id']}/restock", json={"units": [UNIT]}, headers=auth()
    )

    assert res.status_code == 403


def test_restock_takes_specific_cars_in(client, auth, add_vehicle):
    """Restocking a used-car lot means taking named cars in, not raising a count."""
    vehicle = add_vehicle(units=0)

    res = client.post(
        f"/api/vehicles/{vehicle['id']}/restock",
        json={
            "units": [
                {**UNIT, "colour": "Golden Brown", "price": 1010000.0, "year": 2021},
                {**UNIT, "colour": "Jet Black", "price": 1290000.0},
            ]
        },
        headers=_admin(auth),
    )

    assert res.status_code == 200
    body = res.json()
    assert body["restocked"] == 2
    assert body["vehicle"]["quantity"] == 2
    assert body["vehicle"]["price"] == 1010000.0
    assert {unit["colour"] for unit in body["units"]} == {"Golden Brown", "Jet Black"}


def test_restock_requires_at_least_one_car(client, auth, add_vehicle):
    vehicle = add_vehicle()

    res = client.post(
        f"/api/vehicles/{vehicle['id']}/restock", json={"units": []}, headers=_admin(auth)
    )

    assert res.status_code == 400


def test_restock_validates_each_car(client, auth, add_vehicle):
    vehicle = add_vehicle()

    res = client.post(
        f"/api/vehicles/{vehicle['id']}/restock",
        json={"units": [{**UNIT, "price": -5}]},
        headers=_admin(auth),
    )

    assert res.status_code == 400


def test_restock_of_an_unknown_listing_is_404(client, auth):
    res = client.post(
        "/api/vehicles/nope/restock", json={"units": [UNIT]}, headers=_admin(auth)
    )

    assert res.status_code == 404
