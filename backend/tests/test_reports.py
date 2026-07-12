"""Unit tests for the Reports module.

Reports aggregates and exports across every sibling module and drives the
Activity Log and Notification services, so — like the Dashboard suite — the test
database is *unified*: one in-memory SQLite engine holding the Booking,
Maintenance, Asset Audit, Notification and Activity Log tables plus a stand-in
``assets`` table (with the OPTIONAL ``department_id`` / ``category`` columns) that
satisfies the read-only asset reader contract.

Data is seeded with the ORM / Core directly (never through a write endpoint) so
the tests exercise the Reports read, export and UI-backend logic in isolation.
"""
from __future__ import annotations

import csv
import io
from datetime import datetime, timedelta, timezone
from typing import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.reports import register_routes
from app.reports.service import render_csv, render_pdf, reports_service
from app.reports.schemas import ReportColumn

# The Reports router consumes the auth/session seam from the Activity Log module.
from app.audit import deps as reports_deps
from app.audit.deps import Principal, Role

# Import every sibling model so its table registers on its Base.
from app.asset_audit.deps import Base as AuditCycleBase
from app.asset_audit.models import (
    AuditCycle,
    AuditCycleStatus,
    AuditItem,
    AuditItemStatus,
)
from app.audit.deps import Base as ActivityBase
from app.audit.models import ActivityLog, AuditSeverity
from app.booking.deps import Base as BookingBase
from app.booking.models import Booking, BookingStatus
from app.maintenance.deps import Base as MaintenanceBase
from app.maintenance.models import (
    MaintenancePriority,
    MaintenanceRequest,
    MaintenanceStatus,
)
from app.notifications.deps import Base as NotificationBase
from app.notifications.models import Notification, NotificationSeverity, NotificationType

MANAGER_ID = "u-manager"
ADMIN_ID = "u-admin"
EMPLOYEE_ID = "u-employee"
OTHER_ID = "u-other"

NOW = datetime(2026, 7, 12, 10, 0, 0, tzinfo=timezone.utc)
YESTERDAY = NOW - timedelta(days=1)
LAST_WEEK = NOW - timedelta(days=7)

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
    with eng.begin() as conn:
        conn.execute(
            text(
                "CREATE TABLE assets ("
                "id VARCHAR PRIMARY KEY, "
                "name VARCHAR NOT NULL, "
                "status VARCHAR NOT NULL, "
                "department_id VARCHAR, "
                "category VARCHAR)"
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
# Seed helpers
# --------------------------------------------------------------------------- #
def _insert_asset(db, asset_id, status, *, department_id=None, category=None, name=None):
    db.execute(
        text(
            "INSERT INTO assets (id, name, status, department_id, category) "
            "VALUES (:id, :n, :s, :d, :c)"
        ),
        {
            "id": asset_id,
            "n": name or f"Asset {asset_id}",
            "s": status,
            "d": department_id,
            "c": category,
        },
    )


def _add_booking(db, *, status=BookingStatus.PENDING, asset_id="a-1", by=EMPLOYEE_ID, created=NOW, purpose="demo"):
    db.add(
        Booking(
            asset_id=asset_id,
            requested_by=by,
            purpose=purpose,
            start_time=created,
            end_time=created + timedelta(hours=2),
            status=status,
            created_at=created,
        )
    )


def _add_maintenance(db, *, status=MaintenanceStatus.PENDING, priority=MaintenancePriority.MEDIUM, asset_id="a-1", by=EMPLOYEE_ID, created=NOW, issue="broken"):
    db.add(
        MaintenanceRequest(
            asset_id=asset_id,
            raised_by=by,
            priority=priority,
            issue_description=issue,
            status=status,
            created_at=created,
        )
    )


def _add_cycle(db, *, name="Q3", status=AuditCycleStatus.ACTIVE, department_id=None):
    cycle = AuditCycle(
        name=name,
        department_id=department_id,
        start_date=NOW.date(),
        end_date=(NOW + timedelta(days=5)).date(),
        created_by=MANAGER_ID,
        status=status,
    )
    db.add(cycle)
    db.flush()
    return cycle


def _add_item(db, cycle, *, asset_id="a-1", auditor=EMPLOYEE_ID, status=None, created=NOW):
    db.add(
        AuditItem(
            audit_cycle_id=cycle.id,
            asset_id=asset_id,
            auditor_id=auditor,
            status=status,
            created_at=created,
        )
    )


def _add_notification(db, *, recipient=MANAGER_ID, ntype=NotificationType.SYSTEM, severity=NotificationSeverity.INFO, is_read=False, archived=False, created=NOW, title="t", message="m"):
    db.add(
        Notification(
            recipient_id=recipient,
            type=ntype,
            severity=severity,
            title=title,
            message=message,
            is_read=is_read,
            archived=archived,
            created_at=created,
        )
    )


def _add_activity(db, *, actor=MANAGER_ID, action="created", entity_type="booking", entity_id="1", severity=AuditSeverity.INFO, created=NOW, description=None):
    db.add(
        ActivityLog(
            actor_id=actor,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            severity=severity,
            description=description,
            created_at=created,
        )
    )


def make_principal(user_id, role):
    return Principal(id=user_id, role=role)


# --------------------------------------------------------------------------- #
# HTTP client with switchable principal
# --------------------------------------------------------------------------- #
class _Holder:
    def __init__(self, principal):
        self.current = principal


@pytest.fixture()
def client(SessionLocal):
    app = FastAPI()
    register_routes(app)
    holder = _Holder(make_principal(MANAGER_ID, Role.ASSET_MANAGER))

    def override_get_db():
        session = SessionLocal()
        try:
            yield session
        finally:
            session.close()

    def override_get_current_user():
        return holder.current

    app.dependency_overrides[reports_deps.get_db] = override_get_db
    app.dependency_overrides[reports_deps.get_current_user] = override_get_current_user

    test_client = TestClient(app)
    test_client.holder = holder  # type: ignore[attr-defined]
    return test_client


# =========================================================================== #
# Catalogue
# =========================================================================== #
def test_catalog_lists_every_report(client):
    resp = client.get("/api/reports")
    assert resp.status_code == 200
    reports = {entry["report"] for entry in resp.json()}
    assert reports == {
        "asset",
        "booking",
        "maintenance",
        "audit",
        "notification",
        "department",
    }


def test_catalog_describes_filters_and_sort(client):
    entry = next(e for e in client.get("/api/reports").json() if e["report"] == "booking")
    assert entry["searchable"] is True
    assert "status" in entry["filters"]
    assert "created_at" in entry["sortable"]
    assert entry["default_sort"] == "created_at"


# =========================================================================== #
# Booking report — search / filter / sort / pagination
# =========================================================================== #
def _seed_bookings(db):
    _add_booking(db, status=BookingStatus.PENDING, asset_id="a-1", purpose="camera shoot")
    _add_booking(db, status=BookingStatus.APPROVED, asset_id="a-2", purpose="lab work")
    _add_booking(db, status=BookingStatus.PENDING, asset_id="a-3", purpose="camera repair")
    db.commit()


def test_booking_report_returns_rows_and_columns(client, db):
    _seed_bookings(db)
    body = client.get("/api/reports/booking").json()
    assert body["report"] == "booking"
    assert body["meta"]["total"] == 3
    assert {c["key"] for c in body["columns"]} >= {"asset_id", "status", "purpose"}
    assert body["items"][0]["status"] in {"pending", "approved"}


def test_booking_report_filter_by_status(client, db):
    _seed_bookings(db)
    body = client.get("/api/reports/booking?status=pending").json()
    assert body["meta"]["total"] == 2
    assert all(row["status"] == "pending" for row in body["items"])


def test_booking_report_search_matches_purpose(client, db):
    _seed_bookings(db)
    body = client.get("/api/reports/booking?search=camera").json()
    assert body["meta"]["total"] == 2


def test_booking_report_invalid_filter_is_400(client, db):
    _seed_bookings(db)
    resp = client.get("/api/reports/booking?status=nonsense")
    assert resp.status_code == 400


def test_booking_report_sort_and_paginate(client, db):
    _seed_bookings(db)
    p1 = client.get("/api/reports/booking?sort_by=id&order=asc&page=1&page_size=2").json()
    p2 = client.get("/api/reports/booking?sort_by=id&order=asc&page=2&page_size=2").json()
    assert [r["id"] for r in p1["items"]] == [1, 2]
    assert [r["id"] for r in p2["items"]] == [3]
    assert p1["meta"]["pages"] == 2


# =========================================================================== #
# Maintenance report
# =========================================================================== #
def test_maintenance_report_filter_by_priority(client, db):
    _add_maintenance(db, priority=MaintenancePriority.CRITICAL, asset_id="a-1")
    _add_maintenance(db, priority=MaintenancePriority.LOW, asset_id="a-2")
    db.commit()
    body = client.get("/api/reports/maintenance?priority=critical").json()
    assert body["meta"]["total"] == 1
    assert body["items"][0]["priority"] == "critical"


# =========================================================================== #
# Audit report (asset-audit items)
# =========================================================================== #
def test_audit_report_lists_items_with_verdict(client, db):
    cycle = _add_cycle(db)
    _add_item(db, cycle, asset_id="a-1", status=AuditItemStatus.VERIFIED)
    _add_item(db, cycle, asset_id="a-2", status=AuditItemStatus.MISSING)
    _add_item(db, cycle, asset_id="a-3", status=None)
    db.commit()
    body = client.get("/api/reports/audit").json()
    assert body["meta"]["total"] == 3
    missing = client.get("/api/reports/audit?status=missing").json()
    assert missing["meta"]["total"] == 1
    assert missing["items"][0]["asset_id"] == "a-2"


# =========================================================================== #
# Notification report (estate-wide, manager scope)
# =========================================================================== #
def test_notification_report_filters_by_severity(client, db):
    _add_notification(db, recipient="u-a", severity=NotificationSeverity.CRITICAL)
    _add_notification(db, recipient="u-b", severity=NotificationSeverity.INFO)
    db.commit()
    body = client.get("/api/reports/notification?severity=critical").json()
    assert body["meta"]["total"] == 1
    assert body["items"][0]["severity"] == "critical"


# =========================================================================== #
# Asset report (Core-backed, optional columns)
# =========================================================================== #
def test_asset_report_reads_optional_columns(client, db):
    _insert_asset(db, "a-1", "available", department_id="d-1", category="laptop")
    _insert_asset(db, "a-2", "under_maintenance", department_id="d-2", category="camera")
    db.commit()
    body = client.get("/api/reports/asset").json()
    keys = {c["key"] for c in body["columns"]}
    assert {"id", "name", "status", "department_id", "category"} <= keys
    assert body["meta"]["total"] == 2


def test_asset_report_filter_and_search(client, db):
    _insert_asset(db, "a-1", "available", department_id="d-1")
    _insert_asset(db, "a-2", "available", department_id="d-2")
    _insert_asset(db, "b-9", "lost", department_id="d-1")
    db.commit()
    by_status = client.get("/api/reports/asset?status=available").json()
    assert by_status["meta"]["total"] == 2
    by_dept = client.get("/api/reports/asset?department_id=d-1").json()
    assert by_dept["meta"]["total"] == 2
    by_search = client.get("/api/reports/asset?search=b-9").json()
    assert by_search["meta"]["total"] == 1


def test_asset_report_no_table_degrades(client, db):
    db.execute(text("DROP TABLE assets"))
    db.commit()
    body = client.get("/api/reports/asset").json()
    assert body["meta"]["total"] == 0
    assert body["items"] == []


# =========================================================================== #
# Department report (aggregate)
# =========================================================================== #
def test_department_report_aggregates_assets_and_cycles(client, db):
    _insert_asset(db, "a-1", "available", department_id="d-1")
    _insert_asset(db, "a-2", "under_maintenance", department_id="d-1")
    _insert_asset(db, "a-3", "available", department_id="d-2")
    _add_cycle(db, department_id="d-1", status=AuditCycleStatus.ACTIVE)
    _add_cycle(db, department_id="d-1", status=AuditCycleStatus.CLOSED)
    db.commit()

    body = client.get("/api/reports/department?sort_by=department_id&order=asc").json()
    rows = {r["department_id"]: r for r in body["items"]}
    assert rows["d-1"]["total_assets"] == 2
    assert rows["d-1"]["available_assets"] == 1
    assert rows["d-1"]["under_maintenance_assets"] == 1
    assert rows["d-1"]["audit_cycles"] == 2
    assert rows["d-1"]["active_audit_cycles"] == 1
    assert rows["d-2"]["total_assets"] == 1


def test_department_report_search(client, db):
    _insert_asset(db, "a-1", "available", department_id="engineering")
    _insert_asset(db, "a-2", "available", department_id="finance")
    db.commit()
    body = client.get("/api/reports/department?search=eng").json()
    assert body["meta"]["total"] == 1
    assert body["items"][0]["department_id"] == "engineering"


# =========================================================================== #
# Exports
# =========================================================================== #
def test_csv_export_has_header_and_rows(client, db):
    _seed_bookings(db)
    resp = client.get("/api/reports/booking/export?format=csv")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/csv")
    assert "attachment" in resp.headers["content-disposition"]
    assert "booking-report.csv" in resp.headers["content-disposition"]
    reader = list(csv.reader(io.StringIO(resp.text)))
    assert reader[0][0] == "ID"  # label of the id column
    assert len(reader) == 1 + 3  # header + 3 bookings


def test_pdf_export_is_valid_pdf(client, db):
    _seed_bookings(db)
    resp = client.get("/api/reports/booking/export?format=pdf")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"
    assert resp.content.startswith(b"%PDF-1.4")
    assert resp.content.rstrip().endswith(b"%%EOF")


def test_export_respects_filters(client, db):
    _seed_bookings(db)
    resp = client.get("/api/reports/booking/export?format=csv&status=approved")
    reader = list(csv.reader(io.StringIO(resp.text)))
    assert len(reader) == 1 + 1  # header + the single approved booking


def test_pdf_export_paginates_large_reports(db):
    # Unit-level: a report large enough to span multiple PDF pages still assembles.
    cols = [ReportColumn(key="id", label="ID"), ReportColumn(key="v", label="V")]
    rows = [{"id": i, "v": f"row-{i}"} for i in range(200)]
    pdf = render_pdf("Big Report", cols, rows)
    assert pdf.startswith(b"%PDF-1.4")
    assert pdf.count(b"/Type /Page ") >= 2  # more than one page object


def test_render_csv_escapes_and_blanks():
    cols = [ReportColumn(key="a", label="A"), ReportColumn(key="b", label="B")]
    out = render_csv(cols, [{"a": None, "b": "x,y"}]).decode()
    reader = list(csv.reader(io.StringIO(out)))
    assert reader[1] == ["", "x,y"]  # None -> blank; comma stays quoted-safe


# =========================================================================== #
# Activity Log UI backend
# =========================================================================== #
def test_activity_log_filters_and_paginates(client, db):
    _add_activity(db, actor=MANAGER_ID, action="created", created=NOW)
    _add_activity(db, actor=EMPLOYEE_ID, action="deleted", created=YESTERDAY)
    _add_activity(db, actor=MANAGER_ID, action="created", created=LAST_WEEK)
    db.commit()

    all_body = client.get("/api/reports/activity-log").json()
    assert all_body["meta"]["total"] == 3

    by_user = client.get(f"/api/reports/activity-log?user_id={EMPLOYEE_ID}").json()
    assert by_user["meta"]["total"] == 1

    by_action = client.get("/api/reports/activity-log?action=created").json()
    assert by_action["meta"]["total"] == 2


def test_activity_log_date_range(client, db):
    _add_activity(db, action="a", created=NOW)
    _add_activity(db, action="b", created=LAST_WEEK)
    db.commit()
    since = (NOW - timedelta(days=1)).isoformat()
    body = client.get(
        "/api/reports/activity-log", params={"date_from": since}
    ).json()
    assert body["meta"]["total"] == 1


def test_activity_log_rbac_scopes_non_manager(client, db):
    _add_activity(db, actor=MANAGER_ID, action="created")
    _add_activity(db, actor=EMPLOYEE_ID, action="viewed")
    db.commit()
    client.holder.current = make_principal(EMPLOYEE_ID, Role.EMPLOYEE)
    body = client.get("/api/reports/activity-log").json()
    # A non-manager only ever sees their own actions (enforced by the service).
    assert body["meta"]["total"] == 1
    assert body["items"][0]["actor_id"] == EMPLOYEE_ID


# =========================================================================== #
# Notifications UI backend
# =========================================================================== #
def _seed_inbox(db):
    _add_notification(db, recipient=MANAGER_ID, is_read=False, severity=NotificationSeverity.INFO)
    _add_notification(db, recipient=MANAGER_ID, is_read=True, severity=NotificationSeverity.WARNING)
    _add_notification(db, recipient=MANAGER_ID, is_read=False, severity=NotificationSeverity.CRITICAL)
    _add_notification(db, recipient=MANAGER_ID, is_read=True, archived=True)
    _add_notification(db, recipient=OTHER_ID, is_read=False)  # not the caller's
    db.commit()


def test_notifications_views(client, db):
    _seed_inbox(db)
    assert client.get("/api/reports/notifications?view=all").json()["meta"]["total"] == 3
    assert client.get("/api/reports/notifications?view=unread").json()["meta"]["total"] == 2
    assert client.get("/api/reports/notifications?view=read").json()["meta"]["total"] == 1
    assert client.get("/api/reports/notifications?view=critical").json()["meta"]["total"] == 1
    assert client.get("/api/reports/notifications?view=archived").json()["meta"]["total"] == 1


def test_notifications_unread_count(client, db):
    _seed_inbox(db)
    assert client.get("/api/reports/notifications/unread-count").json()["unread"] == 2


def test_notifications_mark_read_and_all(client, db):
    _seed_inbox(db)
    listing = client.get("/api/reports/notifications?view=unread").json()
    first_id = listing["items"][0]["id"]
    marked = client.post(f"/api/reports/notifications/{first_id}/read").json()
    assert marked["is_read"] is True
    assert client.get("/api/reports/notifications/unread-count").json()["unread"] == 1
    assert client.post("/api/reports/notifications/read-all").json()["marked_read"] == 1
    assert client.get("/api/reports/notifications/unread-count").json()["unread"] == 0


def test_notifications_archive(client, db):
    _seed_inbox(db)
    live = client.get("/api/reports/notifications?view=all").json()
    target = live["items"][0]["id"]
    archived = client.post(f"/api/reports/notifications/{target}/archive").json()
    assert archived["archived"] is True
    # It leaves the live inbox and appears in the archive view.
    assert client.get("/api/reports/notifications?view=all").json()["meta"]["total"] == 2
    assert client.get("/api/reports/notifications?view=archived").json()["meta"]["total"] == 2


def test_notifications_only_own_inbox(client, db):
    _seed_inbox(db)
    client.holder.current = make_principal(OTHER_ID, Role.EMPLOYEE)
    body = client.get("/api/reports/notifications?view=all").json()
    assert body["meta"]["total"] == 1


def test_notifications_archive_foreign_is_forbidden(client, db):
    _add_notification(db, recipient=OTHER_ID)
    db.commit()
    # Manager (non-admin) may not touch another user's notification.
    resp = client.post("/api/reports/notifications/1/archive")
    assert resp.status_code == 403


# =========================================================================== #
# RBAC on the report surface
# =========================================================================== #
def test_reports_require_manager(client, db):
    _seed_bookings(db)
    client.holder.current = make_principal(EMPLOYEE_ID, Role.EMPLOYEE)
    assert client.get("/api/reports/booking").status_code == 403
    assert client.get("/api/reports").status_code == 403
    # ...but the personal UI backends stay open to any authenticated user.
    assert client.get("/api/reports/activity-log").status_code == 200
    assert client.get("/api/reports/notifications").status_code == 200


def test_admin_allowed_on_reports(client, db):
    _seed_bookings(db)
    client.holder.current = make_principal(ADMIN_ID, Role.ADMIN)
    assert client.get("/api/reports/booking").status_code == 200


# =========================================================================== #
# Service-level checks for the extended sibling capabilities
# =========================================================================== #
def test_notification_service_archive_is_idempotent(db):
    from app.notifications.service import notification_service

    _add_notification(db, recipient=MANAGER_ID)
    db.commit()
    principal = make_principal(MANAGER_ID, Role.ASSET_MANAGER)
    n1 = notification_service.archive(db, principal, 1)
    stamp = n1.archived_at
    n2 = notification_service.archive(db, principal, 1)  # no-op
    assert n2.archived is True
    assert n2.archived_at == stamp


def test_audit_service_date_range(db):
    from app.audit.service import audit_service

    _add_activity(db, action="x", created=NOW)
    _add_activity(db, action="y", created=LAST_WEEK)
    db.commit()
    principal = make_principal(MANAGER_ID, Role.ASSET_MANAGER)
    rows, total = audit_service.list(
        db, principal, date_from=NOW - timedelta(days=1)
    )
    assert total == 1
    assert rows[0].action == "x"
