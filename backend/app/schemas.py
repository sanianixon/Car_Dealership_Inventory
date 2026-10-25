"""Pydantic request and response models.

Responses use camelCase keys (via serialisation aliases) because the React
frontend consumes them directly.
"""

from datetime import date, datetime
from typing import Annotated, Any

from pydantic import (
    AfterValidator,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    EmailStr,
    Field,
    model_validator,
)


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


def _clean_colours(value: Any) -> Any:
    """Trim colour names and drop repeats.

    Listing "Red", "red" and " Red " as three colours is noise rather than
    information, so they collapse to the first spelling given. A blank name is
    rejected outright: it means the form was submitted wrongly.
    """
    if not isinstance(value, list):
        return value

    seen: set[str] = set()
    cleaned: list[str] = []
    for raw in value:
        if not isinstance(raw, str):
            return value  # let the list[str] rule report the wrong type
        name = raw.strip()
        if not name:
            raise ValueError("colour names cannot be blank")
        if name.casefold() not in seen:
            seen.add(name.casefold())
            cleaned.append(name)
    return cleaned


def _plausible_year(value: int) -> int:
    """Reject a build year that cannot belong to a real vehicle.

    Next year is allowed on purpose: new models reach a forecourt before their
    model year has started.
    """
    latest = date.today().year + 1
    if value < 1900 or value > latest:
        raise ValueError(f"must be between 1900 and {latest}")
    return value


def _not_in_the_future(value: date) -> date:
    """A vehicle cannot have arrived tomorrow. Today is fine."""
    if value > date.today():
        raise ValueError("cannot be a future date")
    return value


Colours = Annotated[
    list[Annotated[str, Field(max_length=40)]],
    BeforeValidator(_clean_colours),
    Field(min_length=1),
]
BuildYear = Annotated[
    int, BeforeValidator(_reject_stringified_number), AfterValidator(_plausible_year)
]
OwnershipNumber = Annotated[
    int, BeforeValidator(_reject_stringified_number), Field(ge=1)
]
AcquisitionDate = Annotated[date, AfterValidator(_not_in_the_future)]


class VehicleCreate(BaseModel):
    """Body of POST /api/vehicles."""

    model_config = ConfigDict(populate_by_name=True)

    make: ShortText
    model: ShortText
    category: ShortText
    price: Price
    quantity: StockQuantity
    year: BuildYear
    colours: Colours
    ownership_number: OwnershipNumber = Field(alias="ownershipNumber")
    acquired_on: AcquisitionDate = Field(alias="acquiredOn")


class VehicleOut(BaseModel):
    """Public view of a vehicle."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    make: str
    model: str
    category: str
    price: float
    quantity: int
    year: int
    colours: list[str]
    ownership_number: int = Field(serialization_alias="ownershipNumber")
    acquired_on: date = Field(serialization_alias="acquiredOn")
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")


class VehicleResponse(BaseModel):
    """Envelope wrapping a single vehicle."""

    vehicle: VehicleOut


class VehicleListResponse(BaseModel):
    """Envelope wrapping a list of vehicles."""

    vehicles: list[VehicleOut]


class VehicleUpdate(BaseModel):
    """Body of PUT /api/vehicles/{id}.

    Every field is optional so a caller can send a subset, but an entirely
    empty body is rejected: it almost always means the caller built the request
    wrongly, and silently succeeding would hide that. Unknown keys such as
    "id" are ignored, so the path alone decides which row is written.
    """

    model_config = ConfigDict(populate_by_name=True)

    make: ShortText | None = None
    model: ShortText | None = None
    category: ShortText | None = None
    price: Price | None = None
    quantity: StockQuantity | None = None
    year: BuildYear | None = None
    colours: Colours | None = None
    ownership_number: OwnershipNumber | None = Field(default=None, alias="ownershipNumber")
    acquired_on: AcquisitionDate | None = Field(default=None, alias="acquiredOn")

    @model_validator(mode="after")
    def _require_one_field(self) -> "VehicleUpdate":
        if not self.changes():
            raise ValueError("at least one field must be supplied")
        return self

    def changes(self) -> dict[str, Any]:
        """The fields the caller actually sent, omitting those left out."""
        return self.model_dump(exclude_none=True)


def _blank_to_none(value: Any) -> Any:
    """Treat an empty or whitespace-only filter as absent.

    A blank box in the search form must widen the results, not narrow them to
    nothing, so it is dropped rather than matched against.
    """
    if isinstance(value, str):
        return value.strip() or None
    return value


# The length limit is attached to the str branch, not to the union: applied to
# "str | None" it would also be checked against None once a blank filter has
# been dropped.
SearchText = Annotated[
    Annotated[str, Field(max_length=100)] | None, BeforeValidator(_blank_to_none)
]


class VehicleSearch(BaseModel):
    """Query parameters for GET /api/vehicles/search.

    Every filter is optional; those supplied are combined with AND.
    """

    model_config = ConfigDict(populate_by_name=True)

    make: SearchText = None
    model: SearchText = None
    category: SearchText = None
    min_price: float | None = Field(default=None, ge=0, alias="minPrice")
    max_price: float | None = Field(default=None, ge=0, alias="maxPrice")

    @model_validator(mode="after")
    def _check_price_range(self) -> "VehicleSearch":
        if (
            self.min_price is not None
            and self.max_price is not None
            and self.min_price > self.max_price
        ):
            # An inverted range can only ever return nothing, so it is
            # reported as a mistake instead of an empty result set.
            raise ValueError("minPrice cannot be greater than maxPrice")
        return self


PurchaseQuantity = Annotated[
    int, BeforeValidator(_reject_stringified_number), Field(ge=1)
]


class PurchaseRequest(BaseModel):
    """Body of POST /api/vehicles/{id}/purchase. Defaults to a single unit."""

    quantity: PurchaseQuantity = 1


class RestockRequest(BaseModel):
    """Body of POST /api/vehicles/{id}/restock. The quantity is mandatory."""

    quantity: PurchaseQuantity


class PurchaseResponse(BaseModel):
    """Envelope returned by a purchase."""

    vehicle: VehicleOut
    purchased: int


class RestockResponse(BaseModel):
    """Envelope returned by a restock."""

    vehicle: VehicleOut
    restocked: int
