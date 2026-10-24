"""Safety paths that the main flows never reach.

These are the branches that only run when something is already wrong: a
malformed hash in the database, a token missing a claim, a misconfigured
deployment, or two registrations racing for one email. They are cheap to test
and they are exactly the paths that turn into a 500 if nobody checks them.
"""

from unittest.mock import patch

import jwt
import pytest

from app.schemas import VehicleSearch
from app.security import JWT_ALGORITHM, jwt_secret, verify_password

CREDENTIALS = {"email": "edge@dealership.com", "password": "Passw0rd!23"}


def test_health_endpoint_reports_ok(client):
    res = client.get("/api/health")

    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_a_validly_signed_token_without_a_subject_is_rejected(client):
    # Correctly signed, so the signature check passes; it simply does not say
    # who it belongs to.
    token = jwt.encode({"role": "admin"}, jwt_secret(), algorithm=JWT_ALGORITHM)

    res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert res.status_code == 401


def test_jwt_secret_prefers_the_configured_value(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", "a-real-secret")

    assert jwt_secret() == "a-real-secret"


def test_jwt_secret_refuses_to_fall_back_in_production(monkeypatch):
    monkeypatch.delenv("JWT_SECRET", raising=False)
    monkeypatch.setenv("APP_ENV", "production")

    # Falling back to the development key in production would let anyone who
    # has read the source mint an admin token.
    with pytest.raises(RuntimeError, match="JWT_SECRET"):
        jwt_secret()


def test_a_malformed_stored_hash_is_a_failed_login_not_a_crash():
    assert verify_password("Passw0rd!23", "not-a-bcrypt-hash") is False


def test_a_blank_search_filter_becomes_absent():
    assert VehicleSearch(make=None).make is None
    assert VehicleSearch(make="   ").make is None
    assert VehicleSearch(make=" Toyota ").make == "Toyota"


def test_losing_the_registration_race_still_returns_409(client):
    """Simulates the outcome of two simultaneous registrations.

    Patching the lookup to find nothing is what a lost race looks like from
    inside the request: the pre-check says the email is free, and the unique
    index disagrees a moment later. That must surface as the same 409, not a
    500 from an unhandled IntegrityError.
    """
    assert client.post("/api/auth/register", json=CREDENTIALS).status_code == 201

    with patch("sqlalchemy.orm.Session.scalar", return_value=None):
        res = client.post("/api/auth/register", json=CREDENTIALS)

    assert res.status_code == 409
    assert res.json()["error"]["message"]
