"""Authentication routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import RegisterRequest, RegisterResponse
from app.security import hash_password

router = APIRouter(prefix="/api/auth", tags=["auth"])

EMAIL_TAKEN = "An account with that email already exists"


def _email_conflict() -> HTTPException:
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=EMAIL_TAKEN)


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> RegisterResponse:
    """Create an account, storing only a bcrypt hash of the password.

    The email has already been normalised by the schema, so the uniqueness
    check is case-insensitive.
    """
    if db.scalar(select(User).where(User.email == payload.email)) is not None:
        raise _email_conflict()

    user = User(email=payload.email, password_hash=hash_password(payload.password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        # The check above is not a guarantee: two concurrent registrations can
        # both pass it and only the unique index will stop the second one.
        # Translate that into the same 409 rather than a 500.
        db.rollback()
        raise _email_conflict()

    db.refresh(user)
    return RegisterResponse(user=user)
