"""Authentication routes."""

import os
import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.schemas import (
    LoginRequest,
    LoginResponse,
    MeResponse,
    RegisterRequest,
    RegisterResponse,
)
from app.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])

EMAIL_TAKEN = "An account with that email already exists"
INVALID_CREDENTIALS = "Invalid email or password"

# Compared against when no account matches, so a login attempt costs the same
# whether or not the email exists. Without this the response time alone would
# reveal which emails are registered.
_TIMING_EQUALISER_HASH = hash_password("timing-equaliser")


def _email_conflict() -> HTTPException:
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=EMAIL_TAKEN)


def _invalid_credentials() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail=INVALID_CREDENTIALS
    )


def _resolve_role(admin_code: str | None) -> str:
    """Decide a new account's role from the supplied invite code.

    No code means an ordinary user. A code is only accepted if one is actually
    configured and matches, so leaving ADMIN_SIGNUP_CODE unset cannot be
    mistaken for "any code is valid". compare_digest avoids leaking how much
    of a guessed code was correct through timing.
    """
    if not admin_code:
        return "user"

    configured = os.getenv("ADMIN_SIGNUP_CODE")
    if not configured or not secrets.compare_digest(admin_code, configured):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Invalid admin signup code"
        )

    return "admin"


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> RegisterResponse:
    """Create an account, storing only a bcrypt hash of the password.

    The email has already been normalised by the schema, so the uniqueness
    check is case-insensitive.
    """
    if db.scalar(select(User).where(User.email == payload.email)) is not None:
        raise _email_conflict()

    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=_resolve_role(payload.admin_code),
    )
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


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    """Exchange credentials for a signed access token.

    An unknown email and a wrong password raise the identical error, so the
    endpoint cannot be used to discover which addresses have accounts.
    """
    user = db.scalar(select(User).where(User.email == payload.email))

    password_hash = user.password_hash if user else _TIMING_EQUALISER_HASH
    password_matches = verify_password(payload.password, password_hash)

    if user is None or not password_matches:
        raise _invalid_credentials()

    return LoginResponse(token=create_access_token(user.id, user.role), user=user)


@router.get("/me", response_model=MeResponse)
def me(user: User = Depends(get_current_user)) -> MeResponse:
    """Return the user the supplied token belongs to."""
    return MeResponse(user=user)
