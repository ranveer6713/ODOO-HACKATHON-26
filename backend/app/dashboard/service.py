"""Dashboard aggregation service.

This is the entire brain of the presentation layer, and it is deliberately thin:
every method issues **read-only, pre-aggregated** SQL against tables owned by the
sibling modules and folds the result into a presentation DTO. No business rule,
state transition, or persistence lives here — the dashboard reports on the estate,
it never changes it.

Design rules honoured throughout:

* **One query per widget.** Each summary is a single ``SELECT`` using conditional
  aggregation (``SUM(CASE ...)``) so a card with five counters costs one round
  trip, never five. Where a widget legitimately spans two tables (audit cycles vs
  audit items) it takes one query per table — never per row.
* **No N+1.** Nothing here loads a collection to count it in Python.
* **No duplicated business logic.** The one place a sibling already exposes the
  exact read we need — the RBAC-scoped, paginated activity feed — we *consume*
  :data:`app.audit.service.audit_service` rather than re-query ``activity_logs``.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import List, Optional, Tuple

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.asset_audit.models import AuditCycle, AuditCycleStatus, AuditItem, AuditItemStatus
from app.audit.models import ActivityLog, AuditSeverity
from app.audit.service import audit_service
from app.booking.models import Booking, BookingStatus
from app.dashboard.deps import Principal, Role
from app.dashboard.gateway import asset_gateway
from app.dashboard.models import AssetKpiBucket, QuickActionKey, bucket_for_status
from app.dashboard.schemas import (
    AssetKpiCards,
    AuditSummary,
    BookingSummary,
    ChartDataPoint,
    ChartSeries,
    DashboardAnalytics,
    DashboardOverview,
    MaintenanceSummary,
    NotificationSummary,
    NotificationTypeCount,
    QuickAction,
    RecentActivityItem,
)
from app.maintenance.models import MaintenanceRequest, MaintenanceStatus
from app.notifications.models import Notification, NotificationType

# Default number of days spanned by the trend charts.
DEFAULT_TREND_DAYS = 30
# Number of most-recent actions shown in the overview's activity feed.
RECENT_ACTIVITY_LIMIT = 20


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _count_when(condition):
    """A ``COALESCE(SUM(CASE WHEN <condition> THEN 1 ELSE 0 END), 0)`` expression.

    Portable conditional aggregation: every counter on a card becomes one column
    of a single row, so the whole card is one query with no dependence on the
    SQL ``FILTER`` clause (unavailable on older SQLite builds).
    """
    return func.coalesce(func.sum(case((condition, 1), else_=0)), 0)


def _day_bounds(now: datetime) -> Tuple[datetime, datetime]:
    """The ``[start, end)`` UTC bounds of the calendar day containing ``now``."""
    start = now.astimezone(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    return start, start + timedelta(days=1)


class DashboardService:
    """Stateless aggregator; the DB session and principal are passed per call."""

    def __init__(self, *, assets=asset_gateway, activity=audit_service) -> None:
        # Dependency-injected collaborators with sensible defaults; no global
        # mutable state, so the singleton is safe to share across requests.
        self._assets = assets
        self._activity = activity

    # ================================================================ KPIs
    def asset_kpis(self, db: Session) -> AssetKpiCards:
        """Headline asset counts, one ``GROUP BY status`` query in the gateway."""
        raw_counts = self._assets.status_counts(db)

        buckets = {bucket: 0 for bucket in AssetKpiBucket}
        for status, count in raw_counts.items():
            buckets[bucket_for_status(status)] += count

        return AssetKpiCards(
            total=sum(raw_counts.values()),
            available=buckets[AssetKpiBucket.AVAILABLE],
            allocated=buckets[AssetKpiBucket.ALLOCATED],
            reserved=buckets[AssetKpiBucket.RESERVED],
            under_maintenance=buckets[AssetKpiBucket.UNDER_MAINTENANCE],
            lost=buckets[AssetKpiBucket.LOST],
            disposed=buckets[AssetKpiBucket.DISPOSED],
            retired=buckets[AssetKpiBucket.RETIRED],
            other=buckets[AssetKpiBucket.OTHER],
        )

    # ============================================================= Bookings
    def booking_summary(
        self, db: Session, *, now: Optional[datetime] = None
    ) -> BookingSummary:
        """Booking counters folded into one conditional-aggregation query."""
        now = now or _utcnow()
        day_start, day_end = _day_bounds(now)

        row = db.execute(
            select(
                func.count(Booking.id),
                _count_when(
                    (Booking.start_time >= day_start)
                    & (Booking.start_time < day_end)
                ),
                _count_when(
                    Booking.status.in_(
                        [BookingStatus.PENDING, BookingStatus.APPROVED]
                    )
                    & (Booking.start_time > now)
                ),
                _count_when(Booking.status == BookingStatus.CHECKED_OUT),
                _count_when(Booking.status == BookingStatus.CHECKED_IN),
                _count_when(Booking.status == BookingStatus.CANCELLED),
            )
        ).one()

        return BookingSummary(
            total=int(row[0]),
            today=int(row[1]),
            upcoming=int(row[2]),
            active=int(row[3]),
            completed=int(row[4]),
            cancelled=int(row[5]),
        )

    # ========================================================== Maintenance
    def maintenance_summary(self, db: Session) -> MaintenanceSummary:
        """Maintenance counters folded into one conditional-aggregation query."""
        S = MaintenanceStatus
        row = db.execute(
            select(
                func.count(MaintenanceRequest.id),
                _count_when(MaintenanceRequest.status == S.PENDING),
                _count_when(MaintenanceRequest.status == S.APPROVED),
                _count_when(MaintenanceRequest.status == S.TECHNICIAN_ASSIGNED),
                _count_when(MaintenanceRequest.status == S.IN_PROGRESS),
                _count_when(MaintenanceRequest.status == S.RESOLVED),
            )
        ).one()

        return MaintenanceSummary(
            total=int(row[0]),
            pending=int(row[1]),
            approved=int(row[2]),
            assigned=int(row[3]),
            in_progress=int(row[4]),
            resolved=int(row[5]),
        )

    # ================================================================ Audit
    def audit_summary(self, db: Session) -> AuditSummary:
        """Audit counters: one query for cycles, one for enrolled items."""
        cycle_row = db.execute(
            select(
                func.count(AuditCycle.id),
                _count_when(AuditCycle.status == AuditCycleStatus.ACTIVE),
            )
        ).one()

        item_row = db.execute(
            select(
                _count_when(AuditItem.status == AuditItemStatus.VERIFIED),
                _count_when(AuditItem.status == AuditItemStatus.MISSING),
                _count_when(AuditItem.status == AuditItemStatus.DAMAGED),
                _count_when(AuditItem.status.is_(None)),
            )
        ).one()

        return AuditSummary(
            audit_cycles=int(cycle_row[0]),
            active_cycles=int(cycle_row[1]),
            verified_assets=int(item_row[0]),
            missing_assets=int(item_row[1]),
            damaged_assets=int(item_row[2]),
            pending_items=int(item_row[3]),
        )

    # ======================================================== Notifications
    def notification_summary(
        self, db: Session, *, now: Optional[datetime] = None
    ) -> NotificationSummary:
        """System-wide notification stats plus the critical-alert signal.

        Two queries for the notification counters (one scalar card, one
        ``GROUP BY type`` breakdown) and one for the critical-alert count drawn
        from the activity trail (notifications carry no severity of their own).
        """
        now = now or _utcnow()
        day_start, day_end = _day_bounds(now)

        row = db.execute(
            select(
                func.count(Notification.id),
                _count_when(Notification.is_read.is_(False)),
                _count_when(
                    (Notification.created_at >= day_start)
                    & (Notification.created_at < day_end)
                ),
            )
        ).one()

        type_rows = db.execute(
            select(Notification.type, func.count(Notification.id)).group_by(
                Notification.type
            )
        ).all()
        counts_by_type = {t: int(c) for t, c in type_rows}
        by_type = [
            NotificationTypeCount(
                type=ntype, count=counts_by_type.get(ntype, 0)
            )
            for ntype in NotificationType
        ]

        critical_alerts = db.execute(
            select(func.count(ActivityLog.id)).where(
                ActivityLog.severity == AuditSeverity.CRITICAL
            )
        ).scalar_one()

        return NotificationSummary(
            total=int(row[0]),
            unread=int(row[1]),
            today=int(row[2]),
            critical_alerts=int(critical_alerts),
            by_type=by_type,
        )

    # ====================================================== Recent activity
    def recent_activity(
        self,
        db: Session,
        principal: Principal,
        *,
        page: int = 1,
        page_size: int = RECENT_ACTIVITY_LIMIT,
    ) -> Tuple[List[RecentActivityItem], int]:
        """Latest actions across the estate, paginated.

        Consumes the Activity Log's own RBAC-scoped, paginated reader rather than
        re-querying ``activity_logs`` — the dashboard adds presentation, not a
        second copy of that access rule.
        """
        entries, total = self._activity.list(
            db,
            principal,
            sort_by="created_at",
            order="desc",
            page=page,
            page_size=page_size,
        )
        items = [
            RecentActivityItem(
                id=entry.id,
                user=entry.actor_id,
                action=entry.action,
                entity_type=entry.entity_type,
                entity_id=entry.entity_id,
                description=entry.description,
                severity=entry.severity,
                timestamp=entry.created_at,
            )
            for entry in entries
        ]
        return items, total

    # ========================================================= Quick actions
    def quick_actions(self) -> List[QuickAction]:
        """The static catalogue of shortcuts (DTOs only — never executed here).

        Each entry points at the owning module's endpoint; that module remains
        the single authority for the behaviour and its authorization. ``required_roles``
        is advisory metadata for the UI, mirroring the owning route's gate.
        """
        return [
            QuickAction(
                key=QuickActionKey.NEW_BOOKING.value,
                label="New booking",
                description="Reserve an asset for a time window.",
                method="POST",
                endpoint="/api/bookings",
                required_roles=[],
            ),
            QuickAction(
                key=QuickActionKey.RAISE_MAINTENANCE.value,
                label="Raise maintenance request",
                description="Report a fault or service need on an asset.",
                method="POST",
                endpoint="/api/maintenance",
                required_roles=[],
            ),
            QuickAction(
                key=QuickActionKey.START_AUDIT_CYCLE.value,
                label="Start audit cycle",
                description="Open a new asset-verification campaign.",
                method="POST",
                endpoint="/api/asset-audit/cycle",
                required_roles=[Role.ASSET_MANAGER.value],
            ),
            QuickAction(
                key=QuickActionKey.REVIEW_PENDING_BOOKINGS.value,
                label="Review pending bookings",
                description="Approve or reject bookings awaiting a decision.",
                method="GET",
                endpoint="/api/bookings?status=pending",
                required_roles=[Role.ASSET_MANAGER.value],
            ),
            QuickAction(
                key=QuickActionKey.REVIEW_PENDING_MAINTENANCE.value,
                label="Review pending maintenance",
                description="Approve or reject maintenance requests.",
                method="GET",
                endpoint="/api/maintenance?status=pending",
                required_roles=[Role.ASSET_MANAGER.value],
            ),
            QuickAction(
                key=QuickActionKey.VIEW_NOTIFICATIONS.value,
                label="View notifications",
                description="Open your notification inbox.",
                method="GET",
                endpoint="/api/notifications",
                required_roles=[],
            ),
        ]

    # ============================================================== Overview
    def overview(
        self,
        db: Session,
        principal: Principal,
        *,
        now: Optional[datetime] = None,
    ) -> DashboardOverview:
        """Compose every widget into one landing payload."""
        now = now or _utcnow()
        recent, _ = self.recent_activity(
            db, principal, page=1, page_size=RECENT_ACTIVITY_LIMIT
        )
        return DashboardOverview(
            generated_at=now,
            kpis=self.asset_kpis(db),
            bookings=self.booking_summary(db, now=now),
            maintenance=self.maintenance_summary(db),
            audit=self.audit_summary(db),
            notifications=self.notification_summary(db, now=now),
            recent_activity=recent,
            quick_actions=self.quick_actions(),
        )

    # ============================================================= Analytics
    def analytics(
        self,
        db: Session,
        *,
        days: int = DEFAULT_TREND_DAYS,
        now: Optional[datetime] = None,
    ) -> DashboardAnalytics:
        """Every chart's data in one payload."""
        now = now or _utcnow()
        return DashboardAnalytics(
            asset_distribution=self.asset_distribution(db),
            department_distribution=self.department_distribution(db),
            maintenance_trend=self.maintenance_trend(db, days=days, now=now),
            booking_trend=self.booking_trend(db, days=days, now=now),
            audit_trend=self.audit_trend(db, days=days, now=now),
        )

    def asset_distribution(self, db: Session) -> ChartSeries:
        """Assets by KPI bucket (one ``GROUP BY status`` query in the gateway)."""
        raw_counts = self._assets.status_counts(db)
        buckets = {bucket: 0 for bucket in AssetKpiBucket}
        for status, count in raw_counts.items():
            buckets[bucket_for_status(status)] += count
        points = [
            ChartDataPoint(label=bucket.value, value=count)
            for bucket, count in buckets.items()
            if count > 0
        ]
        return ChartSeries(name="asset_distribution", points=points)

    def department_distribution(self, db: Session) -> ChartSeries:
        """Assets per department (one query; empty when unsupported)."""
        points = [
            ChartDataPoint(label=dept, value=count)
            for dept, count in self._assets.department_distribution(db)
        ]
        return ChartSeries(name="department_distribution", points=points)

    def maintenance_trend(
        self, db: Session, *, days: int = DEFAULT_TREND_DAYS, now: Optional[datetime] = None
    ) -> ChartSeries:
        return self._daily_trend(
            db,
            column=MaintenanceRequest.created_at,
            name="maintenance_trend",
            days=days,
            now=now,
        )

    def booking_trend(
        self, db: Session, *, days: int = DEFAULT_TREND_DAYS, now: Optional[datetime] = None
    ) -> ChartSeries:
        return self._daily_trend(
            db,
            column=Booking.created_at,
            name="booking_trend",
            days=days,
            now=now,
        )

    def audit_trend(
        self, db: Session, *, days: int = DEFAULT_TREND_DAYS, now: Optional[datetime] = None
    ) -> ChartSeries:
        return self._daily_trend(
            db,
            column=AuditItem.created_at,
            name="audit_trend",
            days=days,
            now=now,
        )

    # --------------------------------------------------------------- helpers
    def _daily_trend(
        self,
        db: Session,
        *,
        column,
        name: str,
        days: int,
        now: Optional[datetime],
    ) -> ChartSeries:
        """A dense per-day count series over the trailing ``days`` window.

        One ``GROUP BY date(column)`` query; days with no rows are back-filled
        with zero in Python so the line chart never has gaps.
        """
        now = now or _utcnow()
        day_start, _ = _day_bounds(now)
        window_start = day_start - timedelta(days=days - 1)

        day_expr = func.date(column)
        rows = db.execute(
            select(day_expr.label("d"), func.count())
            .where(column >= window_start)
            .group_by(day_expr)
        ).all()
        counts = {str(day): int(count) for day, count in rows}

        start_date: date = window_start.date()
        points = [
            ChartDataPoint(
                label=(start_date + timedelta(days=offset)).isoformat(),
                value=counts.get(
                    (start_date + timedelta(days=offset)).isoformat(), 0
                ),
            )
            for offset in range(days)
        ]
        return ChartSeries(name=name, points=points)


# Module-level singleton; stateless, so safe to share across requests.
dashboard_service = DashboardService()
