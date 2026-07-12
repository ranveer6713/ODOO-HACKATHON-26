"""Notifications module (self-contained, reusable vertical slice).

Owns the ``notifications`` table and the recipient-facing inbox. Its
:class:`~app.notifications.service.NotificationService` is the shared delivery
port for the whole backend — Maintenance, Booking and Audit all send messages
through :meth:`NotificationService.notify` (participating in the caller's
transaction so a message commits atomically with the workflow change).

Does **not** own the shared foundation: application bootstrap (``main.py``), the
database engine / ``Base`` / session, JWT auth, RBAC, or the ``users`` table.
Those are consumed through :mod:`app.notifications.deps` and never redefined here.

The foundation owner mounts this module without touching its internals::

    from app.notifications import register_routes
    register_routes(app)
"""
from app.notifications.exceptions import register_exception_handlers
from app.notifications.router import router
from app.notifications.service import notification_service

__all__ = ["router", "register_routes", "notification_service"]


def register_routes(app) -> None:
    """Mount the Notifications router and error handlers onto a FastAPI app."""
    register_exception_handlers(app)
    app.include_router(router)
