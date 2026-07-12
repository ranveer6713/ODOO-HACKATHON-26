"""Asset Audit module (self-contained vertical slice).

Implements the ERP asset-audit workflow and owns two tables:

    * ``audit_cycles`` — an audit campaign scoped to a department/location, run
      over a date range and driven through CREATED -> ACTIVE -> CLOSED.
    * ``audit_items``  — an asset enrolled in a cycle and assigned to an auditor,
      carrying the auditor's Verified / Missing / Damaged verdict.

Workflow::

    create cycle -> assign auditors (enroll assets) -> start -> auditors verify
    every asset -> generate discrepancy report -> close (locks the cycle;
    confirmed-missing assets become LOST via the AssetGateway)

This is **not** the Activity Log — that append-only trail lives in
:mod:`app.audit` and every action here is recorded to it. The Asset ORM model is
never imported; all asset access goes through
:class:`app.asset_audit.gateway.AssetGateway`.

Does **not** own the shared foundation: application bootstrap (``main.py``), the
database engine / ``Base`` / session, JWT auth, RBAC, or the ``users`` / ``assets``
tables. Those are consumed through :mod:`app.asset_audit.deps` and never redefined
here.

The foundation owner mounts this module without touching its internals::

    from app.asset_audit import register_routes
    register_routes(app)
"""
from app.asset_audit.exceptions import register_exception_handlers
from app.asset_audit.router import router
from app.asset_audit.service import asset_audit_service

__all__ = ["router", "register_routes", "asset_audit_service"]


def register_routes(app) -> None:
    """Mount the Asset Audit router and error handlers onto a FastAPI app."""
    register_exception_handlers(app)
    app.include_router(router)
