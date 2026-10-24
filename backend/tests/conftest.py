"""Shared pytest fixtures.

Every test gets its own throwaway SQLite file so tests cannot leak state into
one another. The app's `get_db` dependency is overridden to point at that file.
"""

import os
import tempfile
from typing import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database import Base, get_db
from app.main import app


@pytest.fixture()
def temp_db() -> Iterator[sessionmaker]:
    """Create an empty SQLite file for one test and yield its session factory."""
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)

    engine = create_engine(
        f"sqlite:///{db_path}",
        # timeout: several connections contend for the write lock in the
        # concurrency tests; without it SQLite gives up immediately.
        connect_args={"check_same_thread": False, "timeout": 30},
    )
    Base.metadata.create_all(bind=engine)

    try:
        yield sessionmaker(bind=engine, autoflush=False, autocommit=False)
    finally:
        engine.dispose()
        os.unlink(db_path)


@pytest.fixture()
def client(temp_db: sessionmaker) -> Iterator[TestClient]:
    """An API client wired to this test's own database."""

    def override_get_db() -> Iterator[Session]:
        db = temp_db()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


@pytest.fixture()
def db(temp_db: sessionmaker) -> Iterator[Session]:
    """Direct session on the same database the client uses.

    Lets a test set up or tear down rows that no endpoint exposes, such as
    deleting a user to check that their token stops working.
    """
    session = temp_db()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def auth(client, db):
    """Factory for Authorization headers.

    Promoting the row after sign-in is deliberate: the token is unchanged, yet
    the request is treated as an admin's, which demonstrates that the role is
    read from the database and not from the token's claims.
    """
    from app.models import User

    def _headers(email: str = "member@dealership.com", admin: bool = False) -> dict:
        password = "Passw0rd!23"
        client.post("/api/auth/register", json={"email": email, "password": password})

        if admin:
            db.query(User).filter(User.email == email).update({"role": "admin"})
            db.commit()

        token = client.post(
            "/api/auth/login", json={"email": email, "password": password}
        ).json()["token"]
        return {"Authorization": f"Bearer {token}"}

    return _headers
