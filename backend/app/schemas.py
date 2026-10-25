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


BuildYear = Annotated[
    int, BeforeValidator(_reject_stringified_number), AfterValidator(_plausible_year)
]
OwnershipNumber = Annotated[
    int, BeforeValidator(_reject_stringified_number), Field(ge=1)
]
AcquisitionDate = Annotated[date, AfterValidator(_not_in_the_future)]


class UnitCreate(BaseModel):
    """One car being taken onto the lot."""

    model_config = ConfigDict(populate_by_name=True)

    year: BuildYear
    colour: ShortText
    price: Price
    ownership_number: OwnershipNumber = Field(default=1, alias="ownershipNumber")
    acquired_on: AcquisitionDate = Field(alias="acquiredOn")


class VehicleCreate(BaseModel):
    """Body of POST /api/vehicles.

    A listing is created with the cars that make it up: there is no such thing
    as a model in stock with no actual cars, so at least one unit is required.
    """

    make: ShortText
    model: ShortText
    category: ShortText
    units: list[UnitCreate] = Field(min_length=1)


class UnitOut(BaseModel):
    """Public view of one car."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    year: int
    colour: str
    price: float
    ownership_number: int = Field(serialization_alias="ownershipNumber")
    acquired_on: date = Field(serialization_alias="acquiredOn")
    is_available: bool = Field(serialization_alias="isAvailable")


class VehicleOut(BaseModel):
    """Public view of a listing.

    price and quantity are derived from the available units, not stored, so a
    card can never show stock the lot does not have. price is the cheapest car
    available, which is the figure a forecourt advertises.
    """

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    make: str
    model: str
    category: str
    price: float
    quantity: int
    colours: list[str]
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")


class VehicleDetail(VehicleOut):
    """A listing together with the individual cars behind it."""

    units: list[UnitOut]


class VehicleResponse(BaseModel):
    """Envelope wrapping a single listing."""

    vehicle: VehicleOut


class VehicleDetailResponse(BaseModel):
    """Envelope wrapping a listing and its cars."""

    vehicle: VehicleDetail


class VehicleListResponse(BaseModel):
    """Envelope wrapping a list of listings."""

    vehicles: list[VehicleOut]


class VehicleUpdate(BaseModel):
    """Body of PUT /api/vehicles/{id}.

    Only the listing's own fields. A car's year, colour, price or history is
    changed on the unit, not here, because it does not describe the model.
    """

    make: ShortText | None = None
    model: ShortText | None = None
    category: ShortText | None = None

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


class PurchaseRequest(BaseModel):
    """Body of POST /api/vehicles/{id}/purchase.

    A buyer may name the car they want. Left out, the cheapest available car of
    that model is taken, which is what "buy a Honda City" means on a forecourt
    and keeps the endpoint usable without knowing unit ids.
    """

    model_config = ConfigDict(populate_by_name=True)

    unit_id: str | None = Field(default=None, alias="unitId")


class RestockRequest(BaseModel):
    """Body of POST /api/vehicles/{id}/restock.

    Restocking a used-car lot means taking specific cars in, each with its own
    history and price, so this takes units rather than a count.
    """

    units: list[UnitCreate] = Field(min_length=1)


class PurchaseResponse(BaseModel):
    """Envelope returned by a purchase: the car bought and the listing after."""

    vehicle: VehicleOut
    unit: UnitOut


class RestockResponse(BaseModel):
    """Envelope returned by a restock."""

    vehicle: VehicleOut
    restocked: int
    units: list[UnitOut]
