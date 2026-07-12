"""Domain exceptions for the Dashboard module and their FastAPI handlers.

Framework-agnostic errors raised by the aggregation service, mapped to
consistent JSON by a single handler keyed on this module's own base class so it
never collides with handlers registered by sibling modules or the foundation.
"""
from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse


class DashboardError(Exception):
    """Base class for every error raised by the Dashboard module."""

    status_code: int = 400
    code: str = "dashboard_error"

    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(detail)


class ValidationError(DashboardError):
    status_code = 400
    code = "validation_error"


class PermissionDeniedError(DashboardError):
    status_code = 403
    code = "permission_denied"


class AuthenticationError(DashboardError):
    status_code = 401
    code = "unauthenticated"


async def dashboard_error_handler(
    request: Request, exc: DashboardError
) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.detail}},
    )


def register_exception_handlers(app) -> None:
    """Attach the Dashboard error handler to a FastAPI application."""
    app.add_exception_handler(DashboardError, dashboard_error_handler)
