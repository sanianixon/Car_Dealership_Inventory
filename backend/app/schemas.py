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
    """Body of POST /api/auth/register.

    Note what is absent: there is no role field. The role is derived from the
    invite code server-side, so a caller cannot ask to be an administrator.
    """

    model_config = ConfigDict(populate_by_name=True)

    email: NormalisedEmail
    password: str = Field(min_length=8, max_length=72)
    admin_code: str | None = Field(default=None, alias="adminCode")


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


class LoginRequest(BaseModel):
    """Body of POST /api/auth/login.

    The password deliberately has no length constraint here: rejecting a short
    password with a 400 would tell a caller that the password policy was the
    problem. Login failures must all look identical.
    """

    email: NormalisedEmail
    password: str


class LoginResponse(BaseModel):
    """Envelope returned by a successful login."""

    token: str
    user: UserOut


class MeResponse(BaseModel):
    """Envelope returned by GET /api/auth/me."""

    user: UserOut


def _reject_stringified_number(value: Any) -> Any:
    """Refuse a number supplied as a string.

    Pydantic would happily coerce "18500" to 18500.0. The API contract asks for
    a JSON number, and silently accepting a string hides a bug in the caller.
    """
    if isinstance(value, str):
        raise ValueError("must be a number, not a string")
    return value


def _strip(value: Any) -> Any:
    """Trim a text field so a whitespace-only value fails the length rule."""
    return value.strip() if isinstance(value, str) else value


# Declared once and reused, so every endpoint validates a price, a quantity or
# a name the same way.
ShortText = Annotated[str, BeforeValidator(_strip), Field(min_length=1, max_length=100)]
Price = Annotated[float, BeforeValidator(_reject_stringified_number), Field(ge=0)]
StockQuantity = Annotated[int, BeforeValidator(_reject_stringified_number), Field(ge=0)]


class VehicleCreate(BaseModel):
    """Body of POST /api/vehicles."""

    make: ShortText
    model: ShortText
    category: ShortText
    price: Price
    quantity: StockQuantity


class VehicleOut(BaseModel):
    """Public view of a vehicle."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    make: str
    model: str
    category: str
    price: float
    quantity: int
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")


class VehicleResponse(BaseModel):
    """Envelope wrapping a single vehicle."""

    vehicle: VehicleOut


class VehicleListResponse(BaseModel):
    """Envelope wrapping a list of vehicles."""

    vehicles: list[VehicleOut]
