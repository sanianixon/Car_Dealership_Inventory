"""Tests for GET /api/vehicles/search."""

# Prices are per car, so a listing's price is the cheapest car it still has.
FLEET = [
    {"make": "Maruti", "model": "Swift", "category": "Hatchback",
     "units": [{"price": 650000.0}, {"price": 720000.0}]},
    {"make": "Maruti", "model": "Baleno", "category": "Hatchback",
     "units": [{"price": 780000.0}]},
    {"make": "Hyundai", "model": "Creta", "category": "SUV",
     "units": [{"price": 1850000.0}]},
    {"make": "Mahindra", "model": "Thar", "category": "SUV", "units": 0},
]


def _seed(add_vehicle) -> None:
    for listing in FLEET:
        add_vehicle(**listing)


def _search(client, headers, **params):
    return client.get("/api/vehicles/search", params=params, headers=headers)


def _models(res) -> set[str]:
    return {v["model"] for v in res.json()["vehicles"]}


def test_search_requires_authentication(client):
    assert client.get("/api/vehicles/search").status_code == 401


def test_search_by_make_is_case_insensitive_and_partial(client, auth, add_vehicle):
    headers = auth()
    _seed(add_vehicle)

    res = _search(client, headers, make="maru")

    assert res.status_code == 200
    assert _models(res) == {"Swift", "Baleno"}


def test_search_by_category(client, auth, add_vehicle):
    headers = auth()
    _seed(add_vehicle)

    assert _models(_search(client, headers, category="hatchback")) == {"Swift", "Baleno"}


def test_price_bounds_are_inclusive(client, auth, add_vehicle):
    headers = auth()
    _seed(add_vehicle)

    res = _search(client, headers, minPrice=650000, maxPrice=780000)

    assert _models(res) == {"Swift", "Baleno"}


def test_filters_combine_with_and(client, auth, add_vehicle):
    headers = auth()
    _seed(add_vehicle)

    res = _search(client, headers, make="maruti", category="hatchback")

    assert _models(res) == {"Swift", "Baleno"}


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

    res = _search(client, headers, minPrice=3000000, maxPrice=100000)

    assert res.status_code == 400


def test_search_includes_sold_out_models_when_not_filtering_on_price(
    client, auth, add_vehicle
):
    headers = auth()
    _seed(add_vehicle)

    assert _models(_search(client, headers, make="mahindra")) == {"Thar"}


def test_wildcard_characters_are_matched_literally(client, auth, add_vehicle):
    headers = auth()
    _seed(add_vehicle)
    add_vehicle(make="100%_Electric", model="Bolt")

    # In SQL LIKE, "%" and "_" are wildcards. Unescaped, this query would
    # match every vehicle instead of the one whose name contains the literal
    # characters.
    res = _search(client, headers, make="100%_")

    assert _models(res) == {"Bolt"}


def test_underscore_is_not_a_single_character_wildcard(client, auth, add_vehicle):
    headers = auth()
    _seed(add_vehicle)

    # "_" would match any one character, so unescaped this returns Maruti rows.
    res = _search(client, headers, make="M_ruti")

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


def test_a_price_filter_only_matches_cars_still_for_sale(client, auth, add_vehicle):
    """A price filter asks about the cars, so a sold-out model cannot match.

    Without a price filter the listing still appears, because the dashboard
    needs sold-out models in order to show a disabled Purchase button.
    """
    headers = auth()
    vehicle = add_vehicle(make="Tata", model="Nexon", units=[{"price": 900000.0}])

    assert _models(_search(client, headers, minPrice=800000)) == {"Nexon"}

    client.post(f"/api/vehicles/{vehicle['id']}/purchase", json={}, headers=headers)

    assert _models(_search(client, headers, minPrice=800000)) == set()
    assert _models(_search(client, headers, make="tata")) == {"Nexon"}
