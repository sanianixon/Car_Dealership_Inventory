"""Domain errors raised by the service layer.

These carry no HTTP vocabulary of their own beyond a suggested status code,
which `app.errors` maps to a response. Keeping them separate means a service
can be reused outside a web request without importing FastAPI.
"""

from fastapi import status


class DomainError(Exception):
    """Base class for an expected, reportable business-rule failure."""

    status_code = status.HTTP_400_BAD_REQUEST
    message = "Request could not be completed"

    def __init__(self, message: str | None = None) -> None:
        self.message = message or type(self).message
        super().__init__(self.message)


class VehicleNotFoundError(DomainError):
    status_code = status.HTTP_404_NOT_FOUND
    message = "Vehicle not found"


class OutOfStockError(DomainError):
    status_code = status.HTTP_409_CONFLICT
    message = "Vehicle is out of stock"


class UnitNotFoundError(DomainError):
    status_code = status.HTTP_404_NOT_FOUND
    message = "That vehicle is not listed under this model"


class UnitNotAvailableError(DomainError):
    status_code = status.HTTP_409_CONFLICT
    message = "That vehicle has already been sold"


class DuplicateListingError(DomainError):
    status_code = status.HTTP_409_CONFLICT
    message = "That model is already listed"
