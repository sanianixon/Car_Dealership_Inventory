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


def _register(client, email="login@dealership.com", password="Passw0rd!23"):
    return client.post(
        "/api/auth/register", json={"email": email, "password": password}
    )


def test_login_returns_token_and_user(client):
    _register(client)

    res = client.post(
        "/api/auth/login",
        json={"email": "login@dealership.com", "password": "Passw0rd!23"},
    )

    assert res.status_code == 200
    body = res.json()
    assert body["token"]
    assert body["user"]["email"] == "login@dealership.com"
    assert "password_hash" not in body["user"]


def test_login_token_carries_subject_and_role(client):
    user_id = _register(client).json()["user"]["id"]

    token = client.post(
        "/api/auth/login",
        json={"email": "login@dealership.com", "password": "Passw0rd!23"},
    ).json()["token"]

    from app.security import decode_token

    claims = decode_token(token)
    assert claims["sub"] == user_id
    assert claims["role"] == "user"
    assert "exp" in claims


def test_login_is_case_insensitive_on_email(client):
    _register(client)

    res = client.post(
        "/api/auth/login",
        json={"email": "LOGIN@DEALERSHIP.COM", "password": "Passw0rd!23"},
    )

    assert res.status_code == 200


def test_wrong_password_and_unknown_email_fail_identically(client):
    _register(client)

    wrong_password = client.post(
        "/api/auth/login",
        json={"email": "login@dealership.com", "password": "WrongPassw0rd!"},
    )
    unknown_email = client.post(
        "/api/auth/login",
        json={"email": "nobody@dealership.com", "password": "Passw0rd!23"},
    )

    assert wrong_password.status_code == 401
    assert unknown_email.status_code == 401
    # Identical message: a caller must not be able to discover which emails
    # have accounts by comparing the two responses.
    assert wrong_password.json() == unknown_email.json()
