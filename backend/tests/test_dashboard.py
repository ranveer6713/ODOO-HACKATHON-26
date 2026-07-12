"""Unit tests for the Dashboard aggregation module.

The dashboard aggregates across every sibling module, so — unlike the per-module
suites — the test database is *unified*: one in-memory SQLite engine holding the
Booking, Maintenance, Asset Audit, Notification and Activity Log tables plus a
stand-in ``assets`` table that satisfies the read-only gateway contract. A single
``Session`` bound to that engine can query models from every module's declarative
Base, which is exactly how the shared foundation wires them in production.

Data is seeded with SQLAlchemy Core inserts (never through the sibling services)
so the tests exercise the dashboard's own read/aggregation logic in isolation,
independent of any sibling's write path.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.dashboard import deps, register_routes
from app.dashboard.deps import Principal, Role
from app.dashboard.service import dashboard_service

# Import every sibling model so its table is registered on its Base; each Base's
# metadata is created against the one shared engine below.
from app.asset_audit.deps import Base as AuditCycleBase
from app.asset_audit.models import (  # noqa: F401  (registers tables)
    AuditCycle,
    AuditItem,
)
from app.audit.deps import Base as ActivityBase
from app.audit.models import ActivityLog  # noqa: F401  (registers table)
from app.booking.deps import Base as BookingBase
from app.booking.models import Booking  # noqa: F401  (registers table)
from app.maintenance.deps import Base as MaintenanceBase
from app.maintenance.models import MaintenanceRequest  # noqa: F401
from app.notifications.deps import Base as NotificationBase
from app.notifications.models import Notification  # noqa: F401

MANAGER_ID = "u-manager"
ADMIN_ID = "u-admin"
EMPLOYEE_ID = "u-employee"

# A fixed "now" so day-boundary and trend maths are deterministic.
NOW = datetime(2026, 7, 12, 10, 0, 0, tzinfo=timezone.utc)
TODAY = NOW.replace(hour=0, minute=0, second=0, microsecond=0)
YESTERDAY = TODAY - timedelta(days=1)


_ALL_BASES = (
    BookingBase,
    MaintenanceBase,
    AuditCycleBase,
    NotificationBase,
    ActivityBase,
)


@pytest.fixture()
def engine():
    eng = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    for base in _ALL_BASES:
        base.metadata.create_all(bind=eng)
    # Stand-in for the Asset module's table (foundation-owned in production).
    # Includes the OPTIONAL department_id column so the distribution chart is
    # exercised end-to-end.
    with eng.begin() as conn:
        conn.execute(
            text(
                "CREATE TABLE assets ("
                "id VARCHAR PRIMARY KEY, "
                "name VARCHAR NOT NULL, "
                "status VARCHAR NOT NULL, "
                "department_id VARCHAR)"
            )
        )
    try:
        yield eng
    finally:
        for base in _ALL_BASES:
            base.metadata.drop_all(bind=eng)
        eng.dispose()


@pytest.fixture()
def SessionLocal(engine):
    return sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)


@pytest.fixture()
def db(SessionLocal) -> Iterator[Session]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


# --------------------------------------------------------------------------- #
# Seed helpers (Core inserts — bypass the sibling services deliberately).
# --------------------------------------------------------------------------- #
def _insert_asset(db: Session, asset_id, status, *, department_id=None) -> None:
    db.execute(
        text(
            "INSERT INTO assets (id, name, status, department_id) "
            "VALUES (:id, :n, :s, :d)"
        ),
        {"id": asset_id, "n": f"Asset {asset_id}", "s": status, "d": department_id},
    )


def _insert_booking(db: Session, *, status, start, asset_id="a-1") -> None:
    db.add(
        Booking(
            asset_id=asset_id,
            requested_by=EMPLOYEE_ID,
            purpose="test",
            start_time=start,
            end_time=start + timedelta(hours=2),
            status=status,
            created_at=start,
        )
    )


def _insert_maintenance(db: Session, *, status, created=NOW, asset_id="a-1") -> None:
    db.add(
        MaintenanceRequest(
            asset_id=asset_id,
            raised_by=EMPLOYEE_ID,
            issue_description="broken",
            status=status,
            created_at=created,
        )
    )


def _insert_notification(db: Session, *, ntype, is_read, created=NOW) -> None:
    db.add(
        Notification(
            recipient_id=MANAGER_ID,
            type=ntype,
            title="t",
            message="m",
            is_read=is_read,
            created_at=created,
        )
    )


def _insert_activity(db: Session, *, action, severity, created=NOW, actor=MANAGER_ID) -> None:
    db.add(
        ActivityLog(
            actor_id=actor,
            action=action,
            entity_type="booking",
            entity_id="1",
            severity=severity,
            created_at=created,
        )
    )


def make_principal(user_id: str, role: Role) -> Principal:
    return Principal(id=user_id, role=role)


@pytest.fixture()
def manager() -> Principal:
    return make_principal(MANAGER_ID, Role.ASSET_MANAGER)


@pytest.fixture()
def admin() -> Principal:
    return make_principal(ADMIN_ID, Role.ADMIN)


@pytest.fixture()
def employee() -> Principal:
    return make_principal(EMPLOYEE_ID, Role.EMPLOYEE)


# =========================================================================== #
# Asset KPI cards
# =========================================================================== #
def test_asset_kpis_fold_statuses_into_buckets(db):
    _insert_asset(db, "a-1", "available")
    _insert_asset(db, "a-2", "available")
    _insert_asset(db, "a-3", "booked")  # allocated
    _insert_asset(db, "a-4", "reserved")
    _insert_asset(db, "a-5", "under_maintenance")
    _insert_asset(db, "a-6", "lost")
    _insert_asset(db, "a-7", "disposed")
    _insert_asset(db, "a-8", "retired")
    _insert_asset(db, "a-9", "cancelled")  # unknown bucket -> other
    db.flush()

    kpis = dashboard_service.asset_kpis(db)

    assert kpis.total == 9
    assert kpis.available == 2
    assert kpis.allocated == 1
    assert kpis.reserved == 1
    assert kpis.under_maintenance == 1
    assert kpis.lost == 1
    assert kpis.disposed == 1
    assert kpis.retired == 1
    assert kpis.other == 1
    # Buckets must reconcile to the total.
    parts = (
        kpis.available
        + kpis.allocated
        + kpis.reserved
        + kpis.under_maintenance
        + kpis.lost
        + kpis.disposed
        + kpis.retired
        + kpis.other
    )
    assert parts == kpis.total


def test_asset_kpis_empty_estate_is_all_zero(db):
    kpis = dashboard_service.asset_kpis(db)
    assert kpis.total == 0
    assert kpis.available == 0


def test_asset_kpis_no_assets_table_degrades_to_zero(db):
    # Drop the stand-in table: the gateway must degrade to zeros, not raise.
    db.execute(text("DROP TABLE assets"))
    db.flush()
    kpis = dashboard_service.asset_kpis(db)
    assert kpis.total == 0


# =========================================================================== #
# Booking summary
# =========================================================================== #
def test_booking_summary_counts_each_bucket(db):
    from app.booking.models import BookingStatus

    _insert_booking(db, status=BookingStatus.PENDING, start=NOW)  # today
    _insert_booking(
        db, status=BookingStatus.APPROVED, start=NOW + timedelta(days=3)
    )  # upcoming
    _insert_booking(db, status=BookingStatus.CHECKED_OUT, start=YESTERDAY)  # active
    _insert_booking(db, status=BookingStatus.CHECKED_IN, start=YESTERDAY)  # completed
    _insert_booking(db, status=BookingStatus.CANCELLED, start=YESTERDAY)  # cancelled
    db.flush()

    s = dashboard_service.booking_summary(db, now=NOW)

    assert s.total == 5
    assert s.today == 1
    assert s.upcoming == 1
    assert s.active == 1
    assert s.completed == 1
    assert s.cancelled == 1


def test_booking_summary_empty(db):
    s = dashboard_service.booking_summary(db, now=NOW)
    assert s.total == 0 and s.active == 0 and s.today == 0


# =========================================================================== #
# Maintenance summary
# =========================================================================== #
def test_maintenance_summary_counts_each_status(db):
    from app.maintenance.models import MaintenanceStatus

    _insert_maintenance(db, status=MaintenanceStatus.PENDING)
    _insert_maintenance(db, status=MaintenanceStatus.APPROVED)
    _insert_maintenance(db, status=MaintenanceStatus.TECHNICIAN_ASSIGNED)
    _insert_maintenance(db, status=MaintenanceStatus.IN_PROGRESS)
    _insert_maintenance(db, status=MaintenanceStatus.RESOLVED)
    _insert_maintenance(db, status=MaintenanceStatus.REJECTED)  # not surfaced
    db.flush()

    s = dashboard_service.maintenance_summary(db)

    assert s.total == 6
    assert s.pending == 1
    assert s.approved == 1
    assert s.assigned == 1
    assert s.in_progress == 1
    assert s.resolved == 1


# =========================================================================== #
# Audit summary
# =========================================================================== #
def test_audit_summary_counts_cycles_and_items(db):
    from app.asset_audit.models import (
        AuditCycleStatus,
        AuditItemStatus,
    )
    from datetime import date

    cycle = AuditCycle(
        name="Q3",
        start_date=date(2026, 7, 1),
        end_date=date(2026, 7, 31),
        created_by=MANAGER_ID,
        status=AuditCycleStatus.ACTIVE,
    )
    closed = AuditCycle(
        name="Q2",
        start_date=date(2026, 4, 1),
        end_date=date(2026, 4, 30),
        created_by=MANAGER_ID,
        status=AuditCycleStatus.CLOSED,
    )
    db.add_all([cycle, closed])
    db.flush()

    db.add_all(
        [
            AuditItem(
                audit_cycle_id=cycle.id, asset_id="a-1", auditor_id=MANAGER_ID,
                status=AuditItemStatus.VERIFIED,
            ),
            AuditItem(
                audit_cycle_id=cycle.id, asset_id="a-2", auditor_id=MANAGER_ID,
                status=AuditItemStatus.MISSING,
            ),
            AuditItem(
                audit_cycle_id=cycle.id, asset_id="a-3", auditor_id=MANAGER_ID,
                status=AuditItemStatus.DAMAGED,
            ),
            AuditItem(
                audit_cycle_id=cycle.id, asset_id="a-4", auditor_id=MANAGER_ID,
                status=None,  # not yet verified
            ),
        ]
    )
    db.flush()

    s = dashboard_service.audit_summary(db)

    assert s.audit_cycles == 2
    assert s.active_cycles == 1
    assert s.verified_assets == 1
    assert s.missing_assets == 1
    assert s.damaged_assets == 1
    assert s.pending_items == 1


# =========================================================================== #
# Notification summary
# =========================================================================== #
def test_notification_summary(db):
    from app.notifications.models import NotificationType
    from app.audit.models import AuditSeverity

    _insert_notification(db, ntype=NotificationType.BOOKING, is_read=False)
    _insert_notification(db, ntype=NotificationType.BOOKING, is_read=True)
    _insert_notification(
        db, ntype=NotificationType.MAINTENANCE, is_read=False, created=YESTERDAY
    )
    # Critical alerts are sourced from the activity trail.
    _insert_activity(db, action="delete", severity=AuditSeverity.CRITICAL)
    _insert_activity(db, action="view", severity=AuditSeverity.INFO)
    db.flush()

    s = dashboard_service.notification_summary(db, now=NOW)

    assert s.total == 3
    assert s.unread == 2
    assert s.today == 2  # two created at NOW, one yesterday
    assert s.critical_alerts == 1
    by_type = {c.type: c.count for c in s.by_type}
    assert by_type[NotificationType.BOOKING] == 2
    assert by_type[NotificationType.MAINTENANCE] == 1
    assert by_type[NotificationType.AUDIT] == 0  # dense: all types present


# =========================================================================== #
# Recent activity (reuses the audit service's RBAC-scoped reader)
# =========================================================================== #
def test_recent_activity_orders_newest_first_and_maps_dto(db, manager):
    from app.audit.models import AuditSeverity

    _insert_activity(db, action="old", severity=AuditSeverity.INFO, created=YESTERDAY)
    _insert_activity(db, action="new", severity=AuditSeverity.WARNING, created=NOW)
    db.flush()

    items, total = dashboard_service.recent_activity(db, manager, page=1, page_size=20)

    assert total == 2
    assert items[0].action == "new"  # newest first
    assert items[0].user == MANAGER_ID
    # SQLite has no tz type and returns the stored instant naive; compare the
    # wall-clock value rather than the tzinfo (Postgres would preserve tz).
    assert items[0].timestamp.replace(tzinfo=None) == NOW.replace(tzinfo=None)
    assert items[1].action == "old"


def test_recent_activity_paginates(db, manager):
    from app.audit.models import AuditSeverity

    for i in range(25):
        _insert_activity(
            db,
            action=f"act-{i}",
            severity=AuditSeverity.INFO,
            created=NOW - timedelta(minutes=i),
        )
    db.flush()

    items, total = dashboard_service.recent_activity(db, manager, page=1, page_size=20)
    assert total == 25
    assert len(items) == 20

    page2, _ = dashboard_service.recent_activity(db, manager, page=2, page_size=20)
    assert len(page2) == 5


# =========================================================================== #
# Quick actions (DTOs only)
# =========================================================================== #
def test_quick_actions_are_static_dtos():
    actions = dashboard_service.quick_actions()
    keys = {a.key for a in actions}
    assert "new_booking" in keys
    assert "start_audit_cycle" in keys
    # Every action points at a real owning-module endpoint with a method.
    for a in actions:
        assert a.endpoint.startswith("/api/")
        assert a.method in {"GET", "POST"}


# =========================================================================== #
# Analytics
# =========================================================================== #
def test_asset_distribution_chart(db):
    _insert_asset(db, "a-1", "available")
    _insert_asset(db, "a-2", "available")
    _insert_asset(db, "a-3", "booked")
    db.flush()

    series = dashboard_service.asset_distribution(db)
    points = {p.label: p.value for p in series.points}
    assert points["available"] == 2
    assert points["allocated"] == 1
    # Empty buckets are omitted from the pie.
    assert "lost" not in points


def test_department_distribution_chart(db):
    _insert_asset(db, "a-1", "available", department_id="eng")
    _insert_asset(db, "a-2", "available", department_id="eng")
    _insert_asset(db, "a-3", "available", department_id="ops")
    _insert_asset(db, "a-4", "available", department_id=None)
    db.flush()

    series = dashboard_service.department_distribution(db)
    points = {p.label: p.value for p in series.points}
    assert points["eng"] == 2
    assert points["ops"] == 1
    assert points["Unassigned"] == 1


def test_department_distribution_absent_column_is_empty(db):
    # Recreate assets without the optional department_id column.
    db.execute(text("DROP TABLE assets"))
    db.execute(
        text(
            "CREATE TABLE assets (id VARCHAR PRIMARY KEY, "
            "name VARCHAR NOT NULL, status VARCHAR NOT NULL)"
        )
    )
    db.execute(
        text("INSERT INTO assets (id, name, status) VALUES ('a-1','A','available')")
    )
    db.flush()

    series = dashboard_service.department_distribution(db)
    assert series.points == []


def test_maintenance_trend_is_dense_over_window(db):
    from app.maintenance.models import MaintenanceStatus

    _insert_maintenance(db, status=MaintenanceStatus.PENDING, created=NOW)
    _insert_maintenance(db, status=MaintenanceStatus.PENDING, created=NOW)
    _insert_maintenance(
        db, status=MaintenanceStatus.PENDING, created=NOW - timedelta(days=2)
    )
    db.flush()

    series = dashboard_service.maintenance_trend(db, days=7, now=NOW)

    assert len(series.points) == 7  # one point per day, gaps back-filled
    by_day = {p.label: p.value for p in series.points}
    assert by_day[TODAY.date().isoformat()] == 2
    assert by_day[(TODAY - timedelta(days=2)).date().isoformat()] == 1
    assert by_day[(TODAY - timedelta(days=1)).date().isoformat()] == 0  # gap -> 0


def test_booking_trend_respects_window(db):
    from app.booking.models import BookingStatus

    _insert_booking(db, status=BookingStatus.PENDING, start=NOW)
    # Outside the 7-day window -> excluded.
    _insert_booking(
        db, status=BookingStatus.PENDING, start=NOW - timedelta(days=30)
    )
    db.flush()

    series = dashboard_service.booking_trend(db, days=7, now=NOW)
    total = sum(p.value for p in series.points)
    assert total == 1


def test_analytics_bundles_every_chart(db):
    analytics = dashboard_service.analytics(db, days=14, now=NOW)
    assert analytics.asset_distribution.name == "asset_distribution"
    assert analytics.department_distribution.name == "department_distribution"
    assert len(analytics.maintenance_trend.points) == 14
    assert len(analytics.booking_trend.points) == 14
    assert len(analytics.audit_trend.points) == 14


# =========================================================================== #
# Overview composite
# =========================================================================== #
def test_overview_composes_every_widget(db, manager):
    from app.booking.models import BookingStatus

    _insert_asset(db, "a-1", "available")
    _insert_booking(db, status=BookingStatus.PENDING, start=NOW)
    db.flush()

    overview = dashboard_service.overview(db, manager, now=NOW)

    assert overview.generated_at == NOW
    assert overview.kpis.total == 1
    assert overview.bookings.total == 1
    assert overview.maintenance.total == 0
    assert overview.audit.audit_cycles == 0
    assert overview.notifications.total == 0
    assert overview.quick_actions  # non-empty
    assert isinstance(overview.recent_activity, list)


# =========================================================================== #
# HTTP surface + RBAC
# =========================================================================== #
class _Holder:
    def __init__(self, principal: Principal) -> None:
        self.current = principal


@pytest.fixture()
def client(SessionLocal):
    app = FastAPI()
    register_routes(app)
    holder = _Holder(make_principal(MANAGER_ID, Role.ASSET_MANAGER))

    def override_get_db() -> Iterator[Session]:
        session = SessionLocal()
        try:
            yield session
        finally:
            session.close()

    def override_get_current_user() -> Principal:
        return holder.current

    app.dependency_overrides[deps.get_db] = override_get_db
    app.dependency_overrides[deps.get_current_user] = override_get_current_user

    test_client = TestClient(app)
    test_client.holder = holder  # type: ignore[attr-defined]
    return test_client


def test_overview_endpoint_returns_payload(client):
    resp = client.get("/api/dashboard/overview")
    assert resp.status_code == 200
    body = resp.json()
    assert "kpis" in body
    assert "bookings" in body
    assert "recent_activity" in body
    assert "quick_actions" in body


def test_kpis_endpoint(client):
    resp = client.get("/api/dashboard/kpis")
    assert resp.status_code == 200
    assert resp.json()["total"] == 0


def test_activity_endpoint_is_paginated(client):
    resp = client.get("/api/dashboard/activity?page=1&page_size=5")
    assert resp.status_code == 200
    body = resp.json()
    assert body["meta"]["page"] == 1
    assert body["meta"]["page_size"] == 5


def test_analytics_endpoint_days_validated(client):
    assert client.get("/api/dashboard/analytics?days=7").status_code == 200
    assert client.get("/api/dashboard/analytics?days=0").status_code == 422
    assert client.get("/api/dashboard/analytics?days=999").status_code == 422


def test_quick_actions_endpoint(client):
    resp = client.get("/api/dashboard/quick-actions")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
    assert len(resp.json()) >= 1


def test_employee_is_forbidden(client):
    client.holder.current = make_principal(EMPLOYEE_ID, Role.EMPLOYEE)
    resp = client.get("/api/dashboard/overview")
    assert resp.status_code == 403


def test_admin_is_allowed(client):
    client.holder.current = make_principal(ADMIN_ID, Role.ADMIN)
    resp = client.get("/api/dashboard/overview")
    assert resp.status_code == 200
