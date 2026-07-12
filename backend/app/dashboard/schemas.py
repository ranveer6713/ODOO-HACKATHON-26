"""Pydantic (v2) response schemas for the Dashboard module.

The Dashboard is read-only: it exposes no request bodies, only response DTOs.
Every schema is a flat, presentation-ready projection of aggregated counts —
nothing here carries behaviour or persistence.
"""
from __future__ import annotations

from datetime import datetime
from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field

from app.audit.models import AuditSeverity
from app.notifications.models import NotificationType

T = TypeVar("T")


# ---------------------------------------------------------------------------
# KPI cards
# ---------------------------------------------------------------------------
class AssetKpiCards(BaseModel):
    """Headline asset counts, folded from ``assets.status`` into KPI buckets."""

    total: int = Field(..., ge=0, description="Total assets under management")
    available: int = Field(..., ge=0)
    allocated: int = Field(
        ..., ge=0, description="Currently checked out / in use"
    )
    reserved: int = Field(
        ..., ge=0, description="Held for an upcoming booking (if modelled)"
    )
    under_maintenance: int = Field(..., ge=0)
    lost: int = Field(..., ge=0)
    disposed: int = Field(..., ge=0)
    retired: int = Field(..., ge=0)
    other: int = Field(
        0, ge=0, description="Assets in a status outside the known buckets"
    )


# ---------------------------------------------------------------------------
# Booking summary
# ---------------------------------------------------------------------------
class BookingSummary(BaseModel):
    total: int = Field(..., ge=0)
    today: int = Field(..., ge=0, description="Bookings starting today")
    upcoming: int = Field(
        ..., ge=0, description="Pending/approved bookings starting in the future"
    )
    active: int = Field(..., ge=0, description="Checked out right now")
    completed: int = Field(..., ge=0, description="Checked back in")
    cancelled: int = Field(..., ge=0)


# ---------------------------------------------------------------------------
# Maintenance summary
# ---------------------------------------------------------------------------
class MaintenanceSummary(BaseModel):
    total: int = Field(..., ge=0)
    pending: int = Field(..., ge=0)
    approved: int = Field(..., ge=0)
    assigned: int = Field(
        ..., ge=0, description="A technician has been assigned"
    )
    in_progress: int = Field(..., ge=0)
    resolved: int = Field(..., ge=0)


# ---------------------------------------------------------------------------
# Audit summary
# ---------------------------------------------------------------------------
class AuditSummary(BaseModel):
    audit_cycles: int = Field(..., ge=0, description="Total audit cycles")
    active_cycles: int = Field(..., ge=0, description="Cycles currently active")
    verified_assets: int = Field(..., ge=0)
    missing_assets: int = Field(..., ge=0)
    damaged_assets: int = Field(..., ge=0)
    pending_items: int = Field(
        ..., ge=0, description="Enrolled assets not yet verified"
    )


# ---------------------------------------------------------------------------
# Notification summary
# ---------------------------------------------------------------------------
class NotificationTypeCount(BaseModel):
    type: NotificationType
    count: int = Field(..., ge=0)


class NotificationSummary(BaseModel):
    """System-wide notification stats for the operations dashboard.

    Notifications carry no severity of their own, so ``critical_alerts`` is
    sourced from the canonical system urgency signal — the count of
    CRITICAL-severity entries in the activity trail — and surfaced here so the
    operator sees inbox volume and critical-event volume side by side.
    """

    total: int = Field(..., ge=0)
    unread: int = Field(..., ge=0)
    today: int = Field(..., ge=0, description="Notifications created today")
    critical_alerts: int = Field(
        ..., ge=0, description="CRITICAL-severity activity-log entries"
    )
    by_type: List[NotificationTypeCount] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Recent activity
# ---------------------------------------------------------------------------
class RecentActivityItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user: str = Field(..., description="Actor who performed the action")
    action: str
    entity_type: str
    entity_id: str
    description: Optional[str] = None
    severity: AuditSeverity
    timestamp: datetime


# ---------------------------------------------------------------------------
# Quick actions (DTOs only — the dashboard never executes them)
# ---------------------------------------------------------------------------
class QuickAction(BaseModel):
    key: str = Field(..., description="Stable identifier for the shortcut")
    label: str
    description: str
    method: str = Field(..., description="HTTP method of the target endpoint")
    endpoint: str = Field(..., description="Owning module's endpoint")
    required_roles: List[str] = Field(
        default_factory=list,
        description="Roles the owning module requires to perform the action",
    )


# ---------------------------------------------------------------------------
# Analytics / chart data
# ---------------------------------------------------------------------------
class ChartDataPoint(BaseModel):
    """One labelled value — a pie slice or a single point on a trend line."""

    label: str
    value: int = Field(..., ge=0)


class ChartSeries(BaseModel):
    """A named collection of data points (one chart)."""

    name: str
    points: List[ChartDataPoint] = Field(default_factory=list)


class DashboardAnalytics(BaseModel):
    """Every chart the dashboard renders, in one payload."""

    asset_distribution: ChartSeries
    department_distribution: ChartSeries
    maintenance_trend: ChartSeries
    booking_trend: ChartSeries
    audit_trend: ChartSeries


# ---------------------------------------------------------------------------
# Composite overview
# ---------------------------------------------------------------------------
class DashboardOverview(BaseModel):
    """The full landing payload — every widget in a single round-trip."""

    generated_at: datetime
    kpis: AssetKpiCards
    bookings: BookingSummary
    maintenance: MaintenanceSummary
    audit: AuditSummary
    notifications: NotificationSummary
    recent_activity: List[RecentActivityItem]
    quick_actions: List[QuickAction]


# ---------------------------------------------------------------------------
# Pagination envelope (mirrors the sibling modules)
# ---------------------------------------------------------------------------
class PageMeta(BaseModel):
    total: int = Field(..., description="Total number of matching records")
    page: int = Field(..., description="1-based current page")
    page_size: int = Field(..., description="Records per page")
    pages: int = Field(..., description="Total number of pages")

    @classmethod
    def build(cls, total: int, page: int, page_size: int) -> "PageMeta":
        pages = (total + page_size - 1) // page_size if page_size else 0
        return cls(total=total, page=page, page_size=page_size, pages=pages)


class Page(BaseModel, Generic[T]):
    """Generic paginated response envelope."""

    items: List[T]
    meta: PageMeta
