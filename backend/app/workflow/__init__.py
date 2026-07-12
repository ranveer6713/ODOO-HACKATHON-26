"""Workflow feature module (self-contained).

Owns: Resource Booking, Maintenance Management, Asset Audit, Notifications,
and the workflow-scoped Activity Log entries.

Does NOT own the shared foundation: main.py / application startup, database
engine / Base / Session / get_db, config, JWT & auth, RBAC infrastructure, or
the User / Asset / Department models. Those belong to another developer and are
consumed, never redefined, here.

Person 1 mounts this module without touching its internals:

    from app.workflow import register_routes
    register_routes(app)

or, to compose it under a parent router:

    from app.workflow import get_router
    app.include_router(get_router(), prefix="/api")
"""
from fastapi import APIRouter

from .booking.router import router as booking_router
from .maintenance.router import router as maintenance_router
from .audit.router import router as audit_router


def get_router() -> APIRouter:
    """Return a single aggregated router for the whole Workflow module."""
    router = APIRouter()
    router.include_router(booking_router)
    router.include_router(maintenance_router)
    router.include_router(audit_router)
    return router


def register_routes(app) -> None:
    """Mount all Workflow routes onto the shared FastAPI application."""
    app.include_router(get_router())
