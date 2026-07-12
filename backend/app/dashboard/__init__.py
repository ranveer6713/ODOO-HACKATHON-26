"""Dashboard module (presentation / aggregation layer).

Read-only. Owns **no** tables and implements **no** business rule: every widget
is a pre-aggregated, read-only projection of data owned by the sibling modules —
Booking, Maintenance, Asset Audit, Notifications, the Activity Log — and the
foundation-owned ``assets`` table. Counts and charts are produced with optimized
``GROUP BY`` / conditional-aggregation queries (one query per widget); the
estate-wide activity feed is consumed from
:data:`app.audit.service.audit_service` rather than re-queried.

Because it aggregates across every module, the dashboard depends on the shared
foundation supplying a session over the single unified database (consumed through
:mod:`app.dashboard.deps`). The standalone fallback exists only for import-safety
and isolated unit tests.

The foundation owner mounts this module without touching its internals::

    from app.dashboard import register_routes
    register_routes(app)
"""
from app.dashboard.exceptions import register_exception_handlers
from app.dashboard.router import router
from app.dashboard.service import dashboard_service

__all__ = ["router", "register_routes", "dashboard_service"]


def register_routes(app) -> None:
    """Mount the Dashboard router and error handlers onto a FastAPI app."""
    register_exception_handlers(app)
    app.include_router(router)
