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
