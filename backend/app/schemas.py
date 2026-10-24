"""Pydantic request and response models.

Responses use camelCase keys (via serialisation aliases) because the React
frontend consumes them directly.
"""

from datetime import datetime
from typing import Annotated, Any

from pydantic import BaseModel, BeforeValidator, ConfigDict, EmailStr, Field


def _normalise_email(value: Any) -> Any:
    """Trim surrounding whitespace and lower-case an email before validation.

    Addresses are treated case-insensitively, so one person cannot register
    twice by varying capitalisation.
    """
    return value.strip().lower() if isinstance(value, str) else value


# Reused by every endpoint that accepts an email, so normalisation can never
# be applied in one place and forgotten in another.
NormalisedEmail = Annotated[EmailStr, BeforeValidator(_normalise_email)]


class RegisterRequest(BaseModel):
    """Body of POST /api/auth/register."""

    email: NormalisedEmail
    password: str = Field(min_length=8, max_length=72)


class UserOut(BaseModel):
    """Public view of a user. Deliberately has no password field."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    email: str
    role: str
    created_at: datetime = Field(serialization_alias="createdAt")


class RegisterResponse(BaseModel):
    """Envelope returned by registration."""

    user: UserOut
