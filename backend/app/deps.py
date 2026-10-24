"""Reusable FastAPI dependencies for authentication and authorisation.

Routes declare what they require (`Depends(get_current_user)` or
`Depends(require_admin)`) instead of each one re-reading the Authorization
header, so a protected route cannot forget part of the check.
"""

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.security import decode_token

# auto_error=False so a missing header reaches our handler and returns the
# API's error envelope rather than Starlette's default body.
_bearer = HTTPBearer(auto_error=False)


def _unauthenticated() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    """Resolve the bearer token to a live user row.

    A valid signature is necessary but not sufficient: the subject is looked
    up every request, so a token belonging to a deleted account stops working
    immediately instead of staying usable until it expires.
    """
    if credentials is None or not credentials.credentials:
        raise _unauthenticated()

    try:
        claims = decode_token(credentials.credentials)
    except jwt.PyJWTError:
        raise _unauthenticated()

    user_id = claims.get("sub")
    if not user_id:
        raise _unauthenticated()

    user = db.get(User, user_id)
    if user is None:
        raise _unauthenticated()

    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    """Allow only administrators through.

    The role comes from the database record, never from the token's claim or
    the request body, so an old token cannot keep admin rights after the
    account was demoted.
    """
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator privileges are required",
        )
    return user


def get_vehicle_service(db: Session = Depends(get_db)) -> "VehicleService":
    """Build the vehicle service for one request.

    Assembling the layers here keeps the routes unaware of both the repository
    and the session, and lets a test swap either one out.
    """
    from app.repositories.vehicle_repository import VehicleRepository
    from app.services.vehicle_service import VehicleService

    return VehicleService(VehicleRepository(db))
