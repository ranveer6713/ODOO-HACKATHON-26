"""Dashboard REST endpoints.

Thin by design: every endpoint resolves the current principal / DB session via
dependencies, delegates to :data:`dashboard_service`, and serialises the result.
No aggregation logic lives here — the router only wires HTTP to the service.

The whole surface is read-only and gated to operations roles (asset manager;
admin always). This mirrors the Activity Log's manager scope, so the estate-wide
counters and the recent-activity feed are consistent for everyone who can see
this dashboard.
"""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.dashboard.deps import Principal, Role, get_db, require_roles
from app.dashboard.schemas import (
    AssetKpiCards,
    AuditSummary,
    BookingSummary,
    DashboardAnalytics,
    DashboardOverview,
    MaintenanceSummary,
    NotificationSummary,
    Page,
    PageMeta,
    QuickAction,
    RecentActivityItem,
)
from app.dashboard.service import DEFAULT_TREND_DAYS, RECENT_ACTIVITY_LIMIT, dashboard_service

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

# The dashboard is an operations view: asset managers (and admins, always).
_dashboard_access = require_roles(Role.ASSET_MANAGER)


@router.get("/overview", response_model=DashboardOverview)
def get_overview(
    db: Session = Depends(get_db),
    current: Principal = Depends(_dashboard_access),
) -> DashboardOverview:
    return dashboard_service.overview(db, current)


@router.get("/kpis", response_model=AssetKpiCards)
def get_kpis(
    db: Session = Depends(get_db),
    current: Principal = Depends(_dashboard_access),
) -> AssetKpiCards:
    return dashboard_service.asset_kpis(db)


@router.get("/summary/bookings", response_model=BookingSummary)
def get_booking_summary(
    db: Session = Depends(get_db),
    current: Principal = Depends(_dashboard_access),
) -> BookingSummary:
    return dashboard_service.booking_summary(db)


@router.get("/summary/maintenance", response_model=MaintenanceSummary)
def get_maintenance_summary(
    db: Session = Depends(get_db),
    current: Principal = Depends(_dashboard_access),
) -> MaintenanceSummary:
    return dashboard_service.maintenance_summary(db)


@router.get("/summary/audit", response_model=AuditSummary)
def get_audit_summary(
    db: Session = Depends(get_db),
    current: Principal = Depends(_dashboard_access),
) -> AuditSummary:
    return dashboard_service.audit_summary(db)


@router.get("/summary/notifications", response_model=NotificationSummary)
def get_notification_summary(
    db: Session = Depends(get_db),
    current: Principal = Depends(_dashboard_access),
) -> NotificationSummary:
    return dashboard_service.notification_summary(db)


@router.get("/activity", response_model=Page[RecentActivityItem])
def get_recent_activity(
    page: int = Query(1, ge=1),
    page_size: int = Query(RECENT_ACTIVITY_LIMIT, ge=1, le=100),
    db: Session = Depends(get_db),
    current: Principal = Depends(_dashboard_access),
) -> Page[RecentActivityItem]:
    items, total = dashboard_service.recent_activity(
        db, current, page=page, page_size=page_size
    )
    return Page[RecentActivityItem](
        items=items,
        meta=PageMeta.build(total=total, page=page, page_size=page_size),
    )


@router.get("/quick-actions", response_model=List[QuickAction])
def get_quick_actions(
    current: Principal = Depends(_dashboard_access),
) -> List[QuickAction]:
    return dashboard_service.quick_actions()


@router.get("/analytics", response_model=DashboardAnalytics)
def get_analytics(
    days: int = Query(
        DEFAULT_TREND_DAYS,
        ge=1,
        le=365,
        description="Trailing window (in days) spanned by the trend charts",
    ),
    db: Session = Depends(get_db),
    current: Principal = Depends(_dashboard_access),
) -> DashboardAnalytics:
    return dashboard_service.analytics(db, days=days)
