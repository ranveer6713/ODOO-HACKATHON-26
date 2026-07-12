"""Audit module (self-contained vertical slice).

Owns the ``activity_logs`` table — the append-only audit trail that every
workflow action across the backend writes to via
:meth:`~app.audit.service.AuditService.record`. Managers can flag entries for
review; flagging alerts the actor through the shared
:class:`~app.notifications.service.NotificationService` and is itself recorded to
the trail. Recorded facts are immutable; only the flag/acknowledge review
lifecycle mutates an entry.

Does **not** own the shared foundation: application bootstrap (``main.py``), the
database engine / ``Base`` / session, JWT auth, RBAC, or the ``users`` table.
Those are consumed through :mod:`app.audit.deps` and never redefined here.

The foundation owner mounts this module without touching its internals::

    from app.audit import register_routes
    register_routes(app)
"""
from app.audit.exceptions import register_exception_handlers
from app.audit.router import router
from app.audit.service import audit_service

__all__ = ["router", "register_routes", "audit_service"]


def register_routes(app) -> None:
    """Mount the Audit router and error handlers onto a FastAPI app."""
    register_exception_handlers(app)
    app.include_router(router)
