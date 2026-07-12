"""Domain exceptions for the Maintenance module and their FastAPI handlers.

Services and validators raise these framework-agnostic errors; a single handler
registered by :func:`register_exception_handlers` maps them to consistent JSON
responses with meaningful HTTP status codes. The handler is keyed on this
module's own base class, so it never collides with handlers the shared
foundation may register for its own error hierarchy.
"""
from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse


class MaintenanceError(Exception):
    """Base class for every business-rule error raised by the Maintenance module."""

    status_code: int = 400
    code: str = "maintenance_error"

    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(detail)


class ValidationError(MaintenanceError):
    status_code = 400
    code = "validation_error"


class NotFoundError(MaintenanceError):
    status_code = 404
    code = "not_found"


class ConflictError(MaintenanceError):
    status_code = 409
    code = "conflict"


class PermissionDeniedError(MaintenanceError):
    status_code = 403
    code = "permission_denied"


class AuthenticationError(MaintenanceError):
    status_code = 401
    code = "unauthenticated"


async def maintenance_error_handler(
    request: Request, exc: MaintenanceError
) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.detail}},
    )


def register_exception_handlers(app) -> None:
    """Attach the Maintenance error handler to a FastAPI application."""
    app.add_exception_handler(MaintenanceError, maintenance_error_handler)
