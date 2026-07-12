"""Booking Management module (self-contained vertical slice).

Owns the asset-reservation lifecycle and its state machine:

    PENDING -> APPROVED -> CHECKED_OUT -> CHECKED_IN
    (a pending booking may instead be REJECTED; a pre-checkout booking may be
    CANCELLED)

Enforces the two scheduling rules — a valid time window and no double-booking of
an asset for overlapping periods. Every workflow action is recorded to the audit
trail via :class:`~app.audit.service.AuditService` and notifies the requester
through the shared :class:`~app.notifications.service.NotificationService`. Every
asset interaction goes through :class:`app.booking.gateway.AssetGateway`; the
Asset ORM model is never imported.

Does **not** own the shared foundation: application bootstrap (``main.py``), the
database engine / ``Base`` / session, JWT auth, RBAC, or the ``users`` /
``assets`` tables. Those are consumed through :mod:`app.booking.deps` and never
redefined here.

The foundation owner mounts this module without touching its internals::

    from app.booking import register_routes
    register_routes(app)
"""
from app.booking.exceptions import register_exception_handlers
from app.booking.router import router
from app.booking.service import booking_service

__all__ = ["router", "register_routes", "booking_service"]


def register_routes(app) -> None:
    """Mount the Booking router and error handlers onto a FastAPI app."""
    register_exception_handlers(app)
    app.include_router(router)
