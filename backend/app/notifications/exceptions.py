"""Domain exceptions for the Notifications module and their FastAPI handlers.

Mirrors the per-slice error convention used across the AssetFlow workflow
modules: framework-agnostic errors raised by services/validators, mapped to
consistent JSON by a single handler keyed on this module's own base class so it
never collides with handlers registered by sibling modules or the foundation.
"""
from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse


class NotificationError(Exception):
    """Base class for every business-rule error raised by the Notifications module."""

    status_code: int = 400
    code: str = "notification_error"

    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(detail)


class ValidationError(NotificationError):
    status_code = 400
    code = "validation_error"


class NotFoundError(NotificationError):
    status_code = 404
    code = "not_found"


class PermissionDeniedError(NotificationError):
    status_code = 403
    code = "permission_denied"


class AuthenticationError(NotificationError):
    status_code = 401
    code = "unauthenticated"


async def notification_error_handler(
    request: Request, exc: NotificationError
) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.detail}},
    )


def register_exception_handlers(app) -> None:
    """Attach the Notifications error handler to a FastAPI application."""
    app.add_exception_handler(NotificationError, notification_error_handler)
