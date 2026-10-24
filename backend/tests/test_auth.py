"""Tests for the authentication endpoints."""


def test_register_creates_user(client):
    res = client.post(
        "/api/auth/register",
        json={"email": "buyer@dealership.com", "password": "Passw0rd!23"},
    )

    assert res.status_code == 201
    body = res.json()
    assert body["user"]["email"] == "buyer@dealership.com"
    assert body["user"]["role"] == "user"
    assert "id" in body["user"]
    # A password hash must never leave the API.
    assert "password" not in body["user"]
    assert "password_hash" not in body["user"]


def test_duplicate_email_is_rejected(client):
    payload = {"email": "dupe@dealership.com", "password": "Passw0rd!23"}
    assert client.post("/api/auth/register", json=payload).status_code == 201

    res = client.post("/api/auth/register", json=payload)

    assert res.status_code == 409


def test_email_is_stored_normalised(client):
    res = client.post(
        "/api/auth/register",
        json={"email": "  MiXeD@Dealership.COM  ", "password": "Passw0rd!23"},
    )

    assert res.status_code == 201
    assert res.json()["user"]["email"] == "mixed@dealership.com"


def test_duplicate_differing_only_by_case_is_rejected(client):
    assert (
        client.post(
            "/api/auth/register",
            json={"email": "case@dealership.com", "password": "Passw0rd!23"},
        ).status_code
        == 201
    )

    res = client.post(
        "/api/auth/register",
        json={"email": "CASE@DEALERSHIP.COM", "password": "Passw0rd!23"},
    )

    assert res.status_code == 409
