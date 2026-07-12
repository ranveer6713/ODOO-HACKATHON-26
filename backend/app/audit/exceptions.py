"""Domain exceptions for the Audit module and their FastAPI handlers.

Framework-agnostic errors raised by services/validators, mapped to consistent
JSON by a single handler keyed on this module's own base class so it never
collides with handlers registered by sibling modules or the foundation.
"""
from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse


class AuditError(Exception):
    """Base class for every business-rule error raised by the Audit module."""

    status_code: int = 400
    code: str = "audit_error"

    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(detail)


class ValidationError(AuditError):
    status_code = 400
    code = "validation_error"


class NotFoundError(AuditError):
    status_code = 404
    code = "not_found"


class ConflictError(AuditError):
    status_code = 409
    code = "conflict"


class PermissionDeniedError(AuditError):
    status_code = 403
    code = "permission_denied"


class AuthenticationError(AuditError):
    status_code = 401
    code = "unauthenticated"


async def audit_error_handler(request: Request, exc: AuditError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.detail}},
    )


def register_exception_handlers(app) -> None:
    """Attach the Audit error handler to a FastAPI application."""
    app.add_exception_handler(AuditError, audit_error_handler)
