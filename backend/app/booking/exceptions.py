"""Domain exceptions for the Booking module and their FastAPI handlers.

Framework-agnostic errors raised by services/validators, mapped to consistent
JSON by a single handler keyed on this module's own base class so it never
collides with handlers registered by sibling modules or the foundation.
"""
from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse


class BookingError(Exception):
    """Base class for every business-rule error raised by the Booking module."""

    status_code: int = 400
    code: str = "booking_error"

    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(detail)


class ValidationError(BookingError):
    status_code = 400
    code = "validation_error"


class NotFoundError(BookingError):
    status_code = 404
    code = "not_found"


class ConflictError(BookingError):
    status_code = 409
    code = "conflict"


class PermissionDeniedError(BookingError):
    status_code = 403
    code = "permission_denied"


class AuthenticationError(BookingError):
    status_code = 401
    code = "unauthenticated"


async def booking_error_handler(request: Request, exc: BookingError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.detail}},
    )


def register_exception_handlers(app) -> None:
    """Attach the Booking error handler to a FastAPI application."""
    app.add_exception_handler(BookingError, booking_error_handler)
