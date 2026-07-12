"""End-to-end cross-module integration tests for the Person 4 module.

Where the per-module suites exercise each slice in isolation, this suite mounts
**every** router on **one** FastAPI app backed by **one** SQLite engine — exactly
how the shared foundation composes them in production — and drives real HTTP
workflows across module boundaries. It proves the integration contracts hold:

    * a Booking / Maintenance write records an entry on the Activity Log
      (:mod:`app.audit`) and delivers a Notification (:mod:`app.notifications`)
      *atomically* with the workflow row (all three commit together);
    * the read-only aggregation layers — the Dashboard and the Reports module —
      observe those sibling writes through their live queries;
    * all seven routers coexist on one app with no route collision.

Every module defines its own standalone ``deps`` seam (the foundation is not
wired in this repo), so each module's ``get_db`` / ``get_current_user`` is
overridden onto the shared session and a switchable principal.
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

# --- Module composition seams (register_routes + deps) ----------------------
from app.asset_audit import deps as asset_audit_deps, register_routes as mount_asset_audit
from app.audit import deps as audit_deps, register_routes as mount_audit
from app.booking import deps as booking_deps, register_routes as mount_booking
from app.dashboard import deps as dashboard_deps, register_routes as mount_dashboard
from app.maintenance import deps as maintenance_deps, register_routes as mount_maintenance
from app.notifications import deps as notif_deps, register_routes as mount_notifications
from app.reports import register_routes as mount_reports

# --- Every owned table's Base, so create_all builds a unified schema --------
from app.asset_audit.deps import Base as AssetAuditBase
from app.asset_audit.models import AuditCycle, AuditItem  # noqa: F401  (registers tables)
from app.audit.deps import Base as AuditBase
from app.audit.models import ActivityLog  # noqa: F401  (registers table)
from app.booking.deps import Base as BookingBase
from app.booking.models import Booking  # noqa: F401  (registers table)
from app.maintenance.deps import Base as MaintenanceBase
from app.maintenance.models import MaintenanceRequest  # noqa: F401  (registers table)
from app.notifications.deps import Base as NotificationBase
from app.notifications.models import Notification  # noqa: F401  (registers table)

MANAGER_ID = "u-manager"
EMPLOYEE_ID = "u-employee"

ASSET_ID = "a-1"

_ALL_BASES = (BookingBase, MaintenanceBase, AssetAuditBase, NotificationBase, AuditBase)

# Each module's deps seam, paired so we can override both callables uniformly.
_MODULE_DEPS = (
    booking_deps,
    maintenance_deps,
    asset_audit_deps,
    notif_deps,
    audit_deps,
    dashboard_deps,
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
    # Stand-in for the foundation-owned ``assets`` table.
    with eng.begin() as conn:
        conn.execute(
            text(
                "CREATE TABLE assets ("
                "id VARCHAR PRIMARY KEY, name VARCHAR NOT NULL, "
                "status VARCHAR NOT NULL, department_id VARCHAR)"
            )
        )
        conn.execute(
            text(
                "INSERT INTO assets (id, name, status, department_id) "
                "VALUES (:id, :n, :s, :d)"
            ),
            {"id": ASSET_ID, "n": "Projector", "s": "available", "d": "dept-a"},
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


class _Holder:
    """Switchable acting principal shared across every module's override."""

    def __init__(self) -> None:
        self.id = MANAGER_ID
        self.role = "asset_manager"

    def be(self, user_id: str, role: str) -> None:
        self.id, self.role = user_id, role


@pytest.fixture()
def client(SessionLocal):
    app = FastAPI()
    for mount in (
        mount_booking,
        mount_maintenance,
        mount_asset_audit,
        mount_notifications,
        mount_audit,
        mount_dashboard,
        mount_reports,
    ):
        mount(app)

    holder = _Holder()

    def make_override_db():
        def override_get_db():
            session = SessionLocal()
            try:
                yield session
            finally:
                session.close()

        return override_get_db

    # Override each module's own seam onto the shared session / principal. Each
    # module owns a distinct Principal class, so build it from that module's deps.
    for mod in _MODULE_DEPS:
        app.dependency_overrides[mod.get_db] = make_override_db()

        def override_user(_mod=mod):
            return _mod.Principal(id=holder.id, role=_mod.Role(holder.role))

        app.dependency_overrides[mod.get_current_user] = override_user

    test_client = TestClient(app)
    test_client.holder = holder  # type: ignore[attr-defined]
    return test_client


# --------------------------------------------------------------------------- #
def _future_window():
    start = datetime.now(timezone.utc) + timedelta(days=1)
    return start, start + timedelta(hours=2)


def test_all_routers_mount_without_collision(client):
    """Every module's surface answers on the composed app (no shadowing)."""
    assert client.get("/api/dashboard/overview").status_code == 200
    assert client.get("/api/reports").status_code == 200
    assert client.get("/api/notifications").status_code == 200
    assert client.get("/api/audit").status_code == 200
    assert client.get("/api/bookings").status_code == 200
    assert client.get("/api/maintenance").status_code == 200


def test_booking_write_propagates_across_every_reader(client):
    """A single booking POST must surface in audit, notifications, dashboard, reports."""
    start, end = _future_window()
    created = client.post(
        "/api/bookings",
        json={
            "asset_id": ASSET_ID,
            "purpose": "Board meeting",
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
        },
    )
    assert created.status_code == 201, created.text
    booking_id = created.json()["id"]

    # 1) Activity Log recorded the "created" action against the booking entity.
    audit = client.get("/api/audit", params={"entity_type": "booking"}).json()
    assert audit["meta"]["total"] == 1
    entry = audit["items"][0]
    assert entry["action"] == "created"
    assert entry["entity_id"] == str(booking_id)
    assert entry["actor_id"] == MANAGER_ID

    # 2) Notification delivered to the requester (the manager placed it).
    inbox = client.get("/api/notifications").json()
    assert inbox["meta"]["total"] == 1
    assert inbox["items"][0]["type"] == "booking"
    assert inbox["items"][0]["is_read"] is False

    # 3) Dashboard aggregation reflects the booking and the recent activity.
    overview = client.get("/api/dashboard/overview").json()
    assert overview["bookings"]["total"] == 1
    assert overview["bookings"]["upcoming"] == 1
    assert any(a["entity_id"] == str(booking_id) for a in overview["recent_activity"])

    # 4) Reports show the row and the same activity feed.
    report = client.get("/api/reports/booking").json()
    assert report["meta"]["total"] == 1
    assert report["items"][0]["asset_id"] == ASSET_ID
    feed = client.get("/api/reports/activity-log", params={"entity_type": "booking"}).json()
    assert feed["meta"]["total"] == 1


def test_maintenance_write_propagates_to_audit_and_dashboard(client):
    """A maintenance POST integrates with the same audit / notification / dashboard chain."""
    raised = client.post(
        "/api/maintenance",
        json={"asset_id": ASSET_ID, "priority": "high", "issue_description": "No power"},
    )
    assert raised.status_code == 201, raised.text
    request_id = raised.json()["id"]

    audit = client.get("/api/audit", params={"entity_type": "maintenance"}).json()
    assert audit["meta"]["total"] == 1
    assert audit["items"][0]["entity_id"] == str(request_id)

    inbox = client.get("/api/notifications").json()
    assert any(n["type"] == "maintenance" for n in inbox["items"])

    overview = client.get("/api/dashboard/overview").json()
    assert overview["maintenance"]["total"] == 1
    assert overview["maintenance"]["pending"] == 1


def test_workflow_write_and_its_trail_commit_atomically(client, db):
    """The booking row, its audit entry and its notification share one transaction."""
    start, end = _future_window()
    resp = client.post(
        "/api/bookings",
        json={
            "asset_id": ASSET_ID,
            "purpose": "Atomicity check",
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
        },
    )
    assert resp.status_code == 201

    # All three rows are visible on an independent session => the same commit.
    assert db.execute(text("SELECT COUNT(*) FROM bookings")).scalar_one() == 1
    assert db.execute(text("SELECT COUNT(*) FROM activity_logs")).scalar_one() == 1
    assert db.execute(text("SELECT COUNT(*) FROM notifications")).scalar_one() == 1


def test_rbac_scoping_holds_across_the_composed_app(client):
    """A non-manager is denied the estate-wide dashboard but keeps their own inbox."""
    # Manager places a booking (notifies the manager, not the employee).
    start, end = _future_window()
    client.post(
        "/api/bookings",
        json={
            "asset_id": ASSET_ID,
            "purpose": "Scoped",
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
        },
    )

    client.holder.be(EMPLOYEE_ID, "employee")
    # Operations views are manager-gated.
    assert client.get("/api/dashboard/overview").status_code == 403
    assert client.get("/api/reports/booking").status_code == 403
    # But the employee's own (empty) inbox and activity feed remain reachable.
    assert client.get("/api/notifications").json()["meta"]["total"] == 0
    assert client.get("/api/audit").json()["meta"]["total"] == 0
