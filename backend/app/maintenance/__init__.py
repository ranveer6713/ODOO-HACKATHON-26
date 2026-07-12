"""Maintenance Management module (self-contained vertical slice).

Owns the maintenance request lifecycle and its state machine:

    PENDING -> APPROVED -> TECHNICIAN_ASSIGNED -> IN_PROGRESS -> RESOLVED
    (a pending request may instead be REJECTED)

Does **not** own the shared foundation: application bootstrap (``main.py``), the
database engine / ``Base`` / session, JWT auth, RBAC, or the ``users`` / ``assets``
tables. Those are consumed through :mod:`app.maintenance.deps` and never
redefined here. Every asset interaction goes through
:class:`app.maintenance.gateway.AssetGateway`; the Asset ORM model is never
imported.

The foundation owner mounts this module without touching its internals::

    from app.maintenance import register_routes
    register_routes(app)
"""
from app.maintenance.exceptions import register_exception_handlers
from app.maintenance.router import router

__all__ = ["router", "register_routes"]


def register_routes(app) -> None:
    """Mount the Maintenance router and error handlers onto a FastAPI app."""
    register_exception_handlers(app)
    app.include_router(router)
