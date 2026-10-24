"""Database engine, session factory and the FastAPI session dependency.

The application talks to a real SQLite file (not an in-memory database), so data
survives a restart. The path is configurable so tests and the seed script can
point somewhere else.
"""

import os
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./dealership.db")

# check_same_thread=False is required because FastAPI may serve a single
# connection from more than one thread.
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    """Declarative base shared by every ORM model."""


def get_db() -> Iterator[Session]:
    """Yield a request-scoped session and always close it afterwards."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
