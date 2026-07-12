"""Domain exceptions for the Asset Audit module and their FastAPI handlers.

Services and validators raise these framework-agnostic errors; a single handler
registered by :func:`register_exception_handlers` maps them to consistent JSON
responses with meaningful HTTP status codes. The handler is keyed on this
module's own base class, so it never collides with handlers the shared
foundation (or sibling modules) may register for their own error hierarchies.
"""
from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse


class AssetAuditError(Exception):
    """Base class for every business-rule error raised by the Asset Audit module."""

    status_code: int = 400
    code: str = "asset_audit_error"

    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(detail)


class ValidationError(AssetAuditError):
    status_code = 400
    code = "validation_error"


class NotFoundError(AssetAuditError):
    status_code = 404
    code = "not_found"


class ConflictError(AssetAuditError):
    status_code = 409
    code = "conflict"


class PermissionDeniedError(AssetAuditError):
    status_code = 403
    code = "permission_denied"


class AuthenticationError(AssetAuditError):
    status_code = 401
    code = "unauthenticated"


async def asset_audit_error_handler(
    request: Request, exc: AssetAuditError
) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.detail}},
    )


def register_exception_handlers(app) -> None:
    """Attach the Asset Audit error handler to a FastAPI application."""
    app.add_exception_handler(AssetAuditError, asset_audit_error_handler)
