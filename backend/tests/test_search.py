"""Tests for GET /api/vehicles/search."""

FLEET = [
    {"make": "Toyota", "model": "Corolla", "category": "Sedan", "price": 18500.0, "quantity": 3},
    {"make": "Toyota", "model": "RAV4", "category": "SUV", "price": 32000.0, "quantity": 2},
    {"make": "Honda", "model": "Civic", "category": "Sedan", "price": 22000.0, "quantity": 5},
    {"make": "Ford", "model": "F-150", "category": "Truck", "price": 45000.0, "quantity": 0},
]


def _seed(add_vehicle) -> None:
    for vehicle in FLEET:
        add_vehicle(**vehicle)


def _search(client, headers, **params):
    return client.get("/api/vehicles/search", params=params, headers=headers)


def _models(res) -> set[str]:
    return {v["model"] for v in res.json()["vehicles"]}


def test_search_requires_authentication(client):
    assert client.get("/api/vehicles/search").status_code == 401


def test_search_by_make_is_case_insensitive_and_partial(client, auth, add_vehicle):
    headers = auth()
    _seed(add_vehicle)

    res = _search(client, headers, make="toyo")

    assert res.status_code == 200
    assert _models(res) == {"Corolla", "RAV4"}


def test_search_by_category(client, auth, add_vehicle):
    headers = auth()
    _seed(add_vehicle)

    assert _models(_search(client, headers, category="sedan")) == {"Corolla", "Civic"}


def test_price_bounds_are_inclusive(client, auth, add_vehicle):
    headers = auth()
    _seed(add_vehicle)

    res = _search(client, headers, minPrice=18500, maxPrice=22000)

    assert _models(res) == {"Corolla", "Civic"}


def test_filters_combine_with_and(client, auth, add_vehicle):
    headers = auth()
    _seed(add_vehicle)

    res = _search(client, headers, make="toyota", category="suv")

    assert _models(res) == {"RAV4"}


def test_blank_filters_are_ignored(client, auth, add_vehicle):
    headers = auth()
    _seed(add_vehicle)

    res = _search(client, headers, make="", model="   ", category="")

    assert _models(res) == {v["model"] for v in FLEET}


def test_no_filters_returns_everything(client, auth, add_vehicle):
    headers = auth()
    _seed(add_vehicle)

    assert _models(_search(client, headers)) == {v["model"] for v in FLEET}


def test_min_price_above_max_price_is_rejected(client, auth, add_vehicle):
    headers = auth()
    _seed(add_vehicle)

    res = _search(client, headers, minPrice=30000, maxPrice=10000)

    assert res.status_code == 400


def test_search_includes_sold_out_vehicles(client, auth, add_vehicle):
    headers = auth()
    _seed(add_vehicle)

    assert _models(_search(client, headers, make="ford")) == {"F-150"}


def test_wildcard_characters_are_matched_literally(client, auth, add_vehicle):
    headers = auth()
    _seed(add_vehicle)
    add_vehicle(**{**FLEET[0], "make": "100%_Electric", "model": "Bolt"})

    # In SQL LIKE, "%" and "_" are wildcards. Unescaped, this query would
    # match every vehicle instead of the one whose name contains the literal
    # characters.
    res = _search(client, headers, make="100%_")

    assert _models(res) == {"Bolt"}


def test_underscore_is_not_a_single_character_wildcard(client, auth, add_vehicle):
    headers = auth()
    _seed(add_vehicle)

    # "_" would match any one character, so unescaped this returns Toyota rows.
    res = _search(client, headers, make="T_yota")

    assert _models(res) == set()


def test_sql_injection_attempt_is_inert(client, auth, add_vehicle):
    headers = auth()
    _seed(add_vehicle)

    res = _search(client, headers, make="'; DROP TABLE vehicles; --")

    assert res.status_code == 200
    assert _models(res) == set()
    # The table must still be there afterwards.
    assert client.get("/api/vehicles", headers=headers).status_code == 200
    assert len(client.get("/api/vehicles", headers=headers).json()["vehicles"]) == len(FLEET)
