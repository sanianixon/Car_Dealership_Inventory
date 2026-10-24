"""Tests for token-based identity: GET /api/auth/me and the admin invite code."""

import pytest

from app.models import User

CREDENTIALS = {"email": "me@dealership.com", "password": "Passw0rd!23"}


def _register_and_login(client, **overrides) -> str:
    payload = {**CREDENTIALS, **overrides}
    client.post("/api/auth/register", json=payload)
    res = client.post(
        "/api/auth/login",
        json={"email": payload["email"], "password": payload["password"]},
    )
    return res.json()["token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_me_requires_a_token(client):
    assert client.get("/api/auth/me").status_code == 401


def test_me_returns_the_signed_in_user(client):
    token = _register_and_login(client)

    res = client.get("/api/auth/me", headers=_auth(token))

    assert res.status_code == 200
    assert res.json()["user"]["email"] == CREDENTIALS["email"]


def test_me_rejects_a_tampered_token(client):
    token = _register_and_login(client)

    res = client.get("/api/auth/me", headers=_auth(token + "x"))

    assert res.status_code == 401


def test_me_rejects_a_token_whose_user_was_deleted(client, db):
    token = _register_and_login(client)

    db.query(User).delete()
    db.commit()

    # The signature is still valid, so the token must be checked against the
    # database, not trusted on its own.
    assert client.get("/api/auth/me", headers=_auth(token)).status_code == 401


def test_role_cannot_be_escalated_from_the_request_body(client):
    res = client.post(
        "/api/auth/register",
        json={**CREDENTIALS, "role": "admin"},
    )

    assert res.status_code == 201
    assert res.json()["user"]["role"] == "user"


def test_matching_admin_code_grants_the_admin_role(client, monkeypatch):
    monkeypatch.setenv("ADMIN_SIGNUP_CODE", "let-me-in")

    res = client.post(
        "/api/auth/register",
        json={**CREDENTIALS, "adminCode": "let-me-in"},
    )

    assert res.status_code == 201
    assert res.json()["user"]["role"] == "admin"


def test_wrong_admin_code_is_forbidden(client, monkeypatch):
    monkeypatch.setenv("ADMIN_SIGNUP_CODE", "let-me-in")

    res = client.post(
        "/api/auth/register",
        json={**CREDENTIALS, "adminCode": "guessing"},
    )

    assert res.status_code == 403


def test_admin_code_is_rejected_when_none_is_configured(client, monkeypatch):
    monkeypatch.delenv("ADMIN_SIGNUP_CODE", raising=False)

    res = client.post(
        "/api/auth/register",
        json={**CREDENTIALS, "adminCode": "anything"},
    )

    # An unconfigured code must not mean "any code works".
    assert res.status_code == 403
