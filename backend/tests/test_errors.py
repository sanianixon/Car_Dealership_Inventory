"""Tests for the uniform API error envelope.

Every error must look like {"error": {"message": ..., "details": [...]}} so the
frontend has exactly one shape to parse. FastAPI's default is {"detail": ...}.
"""


def test_handled_error_uses_error_envelope(client):
    payload = {"email": "shape@dealership.com", "password": "Passw0rd!23"}
    client.post("/api/auth/register", json=payload)

    res = client.post("/api/auth/register", json=payload)

    assert res.status_code == 409
    body = res.json()
    assert "detail" not in body
    assert isinstance(body["error"]["message"], str)
    assert body["error"]["message"]


def test_validation_error_returns_400_with_field_details(client):
    res = client.post(
        "/api/auth/register",
        json={"email": "not-an-email", "password": "short"},
    )

    # The API contract uses 400 for validation, not FastAPI's default 422.
    assert res.status_code == 400
    body = res.json()
    assert body["error"]["message"]
    paths = [d["path"] for d in body["error"]["details"]]
    assert "email" in paths
    assert "password" in paths
    # The "body" prefix of FastAPI's loc tuple must not leak into the path.
    assert all(not p.startswith("body") for p in paths)


def test_unknown_route_uses_error_envelope(client):
    res = client.get("/api/does-not-exist")

    assert res.status_code == 404
    assert "error" in res.json()
