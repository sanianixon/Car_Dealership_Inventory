"""Password hashing and JSON Web Token issuing/verification.

Only the password hash is ever stored or returned; the plaintext is used once,
in memory, and then discarded.
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt

# bcrypt truncates anything past 72 bytes, so the schema caps the password
# length rather than letting a longer password be silently shortened.
MAX_PASSWORD_BYTES = 72

JWT_ALGORITHM = "HS256"
TOKEN_TTL = timedelta(hours=8)

_DEV_SECRET = "dev-secret-do-not-use-in-production"


def jwt_secret() -> str:
    """Return the signing secret.

    Read at call time rather than import time so tests and deployments can set
    it without re-importing the module. A real secret is mandatory outside
    development: a predictable key would let anyone mint an admin token.
    """
    secret = os.getenv("JWT_SECRET")
    if secret:
        return secret
    if os.getenv("APP_ENV", "development").lower() == "production":
        raise RuntimeError("JWT_SECRET must be set when APP_ENV=production")
    return _DEV_SECRET


def hash_password(password: str) -> str:
    """Hash a plaintext password with a per-password random salt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Check a plaintext password against a stored hash in constant time."""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        # Malformed/legacy hash in the database: treat as a failed login
        # rather than a 500.
        return False


def create_access_token(user_id: str, role: str) -> str:
    """Mint a signed token identifying the user and their role.

    The token is signed, not encrypted: the claims are readable by anyone
    holding it, so it carries an id and a role and never anything secret.
    """
    now = datetime.now(timezone.utc)
    claims = {"sub": user_id, "role": role, "iat": now, "exp": now + TOKEN_TTL}
    return jwt.encode(claims, jwt_secret(), algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    """Verify a token's signature and expiry and return its claims.

    Raises jwt.PyJWTError if the token is tampered with, expired or unsigned.
    """
    return jwt.decode(token, jwt_secret(), algorithms=[JWT_ALGORITHM])
