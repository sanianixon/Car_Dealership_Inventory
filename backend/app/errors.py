"""A single error shape for the whole API.

FastAPI's default error body is {"detail": ...} and its validation failures are
422. The frontend expects one envelope and 400 for validation, so both are
translated here rather than in every route.
"""

from typing import Any, Iterable

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

# FastAPI reports the location of a bad field as a tuple like
# ("body", "price"). The caller only cares about the field name.
_LOCATION_PREFIXES = {"body", "query", "path", "header", "cookie"}


def _field_path(location: Iterable[Any]) -> str:
    """Render a validation error location as a dotted field path."""
    parts = [str(part) for part in location]
    if parts and parts[0] in _LOCATION_PREFIXES:
        parts = parts[1:]
    return ".".join(parts)


def error_body(message: str, details: list[dict[str, str]] | None = None) -> dict:
    """Build the API's error envelope."""
    error: dict[str, Any] = {"message": message}
    if details:
        error["details"] = details
    return {"error": error}


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Render any raised HTTPException in the envelope."""
    return JSONResponse(
        status_code=exc.status_code,
        content=error_body(str(exc.detail)),
        headers=getattr(exc, "headers", None),
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Render a request validation failure as a 400 listing each bad field."""
    details = [
        {"path": _field_path(err.get("loc", ())), "message": err.get("msg", "Invalid value")}
        for err in exc.errors()
    ]
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=error_body("Validation failed", details),
    )


def register_error_handlers(app: FastAPI) -> None:
    """Attach the handlers to an app. Called once, from main."""
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
