"""Tests for purchasing and restocking, including concurrent purchases."""

from concurrent.futures import ThreadPoolExecutor

VALID = {
    "make": "Toyota",
    "model": "Corolla",
    "category": "Sedan",
    "price": 18500.0,
    "quantity": 3,
}


def _create(client, headers, **overrides) -> dict:
    return client.post(
        "/api/vehicles", json={**VALID, **overrides}, headers=headers
    ).json()["vehicle"]


def test_purchase_requires_authentication(client, auth):
    vehicle = _create(client, auth())

    assert client.post(f"/api/vehicles/{vehicle['id']}/purchase").status_code == 401


def test_purchase_defaults_to_one_unit(client, auth):
    headers = auth()
    vehicle = _create(client, headers)

    res = client.post(f"/api/vehicles/{vehicle['id']}/purchase", json={}, headers=headers)

    assert res.status_code == 200
    body = res.json()
    assert body["purchased"] == 1
    assert body["vehicle"]["quantity"] == 2


def test_purchase_with_an_explicit_quantity(client, auth):
    headers = auth()
    vehicle = _create(client, headers)

    res = client.post(
        f"/api/vehicles/{vehicle['id']}/purchase", json={"quantity": 3}, headers=headers
    )

    assert res.status_code == 200
    assert res.json()["vehicle"]["quantity"] == 0


def test_purchasing_a_sold_out_vehicle_is_rejected(client, auth):
    headers = auth()
    vehicle = _create(client, headers, quantity=0)

    res = client.post(f"/api/vehicles/{vehicle['id']}/purchase", json={}, headers=headers)

    assert res.status_code == 409
    assert res.json()["error"]["message"] == "Vehicle is out of stock"


def test_purchasing_more_than_available_is_rejected(client, auth):
    headers = auth()
    vehicle = _create(client, headers, quantity=2)

    res = client.post(
        f"/api/vehicles/{vehicle['id']}/purchase", json={"quantity": 5}, headers=headers
    )

    assert res.status_code == 409
    # The failed purchase must not have changed the stock.
    assert (
        client.get(f"/api/vehicles/{vehicle['id']}", headers=headers).json()["vehicle"][
            "quantity"
        ]
        == 2
    )


def test_purchase_rejects_a_non_positive_quantity(client, auth):
    headers = auth()
    vehicle = _create(client, headers)

    for quantity in (0, -1):
        res = client.post(
            f"/api/vehicles/{vehicle['id']}/purchase",
            json={"quantity": quantity},
            headers=headers,
        )
        assert res.status_code == 400


def test_purchase_unknown_vehicle_is_404(client, auth):
    res = client.post("/api/vehicles/nope/purchase", json={}, headers=auth())

    assert res.status_code == 404


def test_concurrent_purchases_never_oversell(client, auth):
    """The test this phase exists for.

    Ten callers try to buy the single unit in stock at the same time. A
    read-then-write implementation lets several of them pass the stock check
    before any of them writes, and the quantity goes negative.
    """
    headers = auth()
    vehicle = _create(client, headers, quantity=1)
    attempts = 10

    def buy(_: int):
        return client.post(
            f"/api/vehicles/{vehicle['id']}/purchase", json={"quantity": 1}, headers=headers
        ).status_code

    with ThreadPoolExecutor(max_workers=attempts) as pool:
        statuses = list(pool.map(buy, range(attempts)))

    assert statuses.count(200) == 1
    assert statuses.count(409) == attempts - 1
    # No request may have failed for any other reason, a 500 included.
    assert set(statuses) == {200, 409}

    remaining = client.get(f"/api/vehicles/{vehicle['id']}", headers=headers).json()
    assert remaining["vehicle"]["quantity"] == 0


def test_restock_requires_authentication(client, auth):
    vehicle = _create(client, auth())

    assert (
        client.post(f"/api/vehicles/{vehicle['id']}/restock", json={"quantity": 1}).status_code
        == 401
    )


def test_restock_is_forbidden_for_a_non_admin(client, auth):
    headers = auth()
    vehicle = _create(client, headers)

    res = client.post(
        f"/api/vehicles/{vehicle['id']}/restock", json={"quantity": 5}, headers=headers
    )

    assert res.status_code == 403


def test_restock_as_admin_increases_quantity(client, auth):
    member = auth()
    admin = auth(email="boss@dealership.com", admin=True)
    vehicle = _create(client, member, quantity=0)

    res = client.post(
        f"/api/vehicles/{vehicle['id']}/restock", json={"quantity": 7}, headers=admin
    )

    assert res.status_code == 200
    body = res.json()
    assert body["restocked"] == 7
    assert body["vehicle"]["quantity"] == 7


def test_restock_requires_a_quantity(client, auth):
    admin = auth(email="boss@dealership.com", admin=True)
    vehicle = _create(client, admin)

    res = client.post(f"/api/vehicles/{vehicle['id']}/restock", json={}, headers=admin)

    assert res.status_code == 400


def test_restock_rejects_a_non_positive_quantity(client, auth):
    admin = auth(email="boss@dealership.com", admin=True)
    vehicle = _create(client, admin)

    for quantity in (0, -3):
        res = client.post(
            f"/api/vehicles/{vehicle['id']}/restock",
            json={"quantity": quantity},
            headers=admin,
        )
        assert res.status_code == 400


def test_restock_unknown_vehicle_is_404(client, auth):
    admin = auth(email="boss@dealership.com", admin=True)

    res = client.post("/api/vehicles/nope/restock", json={"quantity": 1}, headers=admin)

    assert res.status_code == 404
