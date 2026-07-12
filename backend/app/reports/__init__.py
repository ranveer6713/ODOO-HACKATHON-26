"""Reports module (presentation / aggregation + UI-backend layer).

Read-only aggregation like the Dashboard, plus two UI backends. It owns **no**
tables and implements **no** business rule:

* six tabular **reports** (Asset, Booking, Maintenance, Audit, Notification,
  Department) with search / filter / sort / pagination and CSV + PDF export,
  produced with optimized database queries;
* the **Activity Log UI backend**, which consumes
  :data:`app.audit.service.audit_service`;
* the **Notifications UI backend**, which consumes
  :data:`app.notifications.service.notification_service`.

Because it aggregates across modules and drives sibling services, Reports relies
on the shared foundation supplying a session over the single unified database.

The foundation owner mounts this module without touching its internals::

    from app.reports import register_routes
    register_routes(app)
"""
from app.reports.router import router
from app.reports.service import reports_service

__all__ = ["router", "register_routes", "reports_service"]


def register_routes(app) -> None:
    """Mount the Reports router (and the consumed modules' error handlers).

    The Notifications / Activity Log services this module drives raise their own
    domain exceptions; registering their handlers here means those errors map to
    the correct HTTP status even when Reports is mounted in isolation. In a full
    application the owning modules register the identical handlers, so this is
    redundant-but-harmless (same handler keyed on the same exception class).
    """
    from app.audit.exceptions import register_exception_handlers as _audit_handlers
    from app.notifications.exceptions import (
        register_exception_handlers as _notification_handlers,
    )

    _audit_handlers(app)
    _notification_handlers(app)
    app.include_router(router)
