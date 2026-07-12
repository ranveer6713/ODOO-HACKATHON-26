"""Unit and API tests for the Asset Audit module.

Exercised in complete isolation: an in-memory SQLite database holds the
module-owned ``audit_cycles`` / ``audit_items`` tables, the sibling
``activity_logs`` and ``notifications`` tables (every action logs + notifies),
plus a stand-in ``assets`` table satisfying the AssetGateway contract
(``id``, ``name``, ``status``). Foundation dependencies are overridden.

Covers the full state machine and every business rule:
    * A closed audit cannot be edited (cycle or items)
    * An asset cannot be verified twice in a cycle
    * One asset appears only once per cycle (no duplicate asset)
    * No duplicate auditor entry
    * An empty audit cannot be closed
    * Discrepancy report generated automatically
    * Confirmed-missing assets become LOST via AssetGateway
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.asset_audit import deps, register_routes
from app.asset_audit.deps import Base, Principal, Role
from app.asset_audit.exceptions import (
    NotFoundError,
    PermissionDeniedError,
    ValidationError,
)
from app.asset_audit.models import (
    AuditCycle,  # noqa: F401  (registers table)
    AuditCycleStatus,
    AuditItem,  # noqa: F401  (registers table)
    AuditItemStatus,
)
from app.asset_audit.schemas import (
    AuditCycleCreate,
    AuditCycleUpdate,
    AuditItemCreate,
    AuditItemVerify,
)
from app.asset_audit.service import asset_audit_service as svc

# Sibling tables that audit actions write to.
from app.audit.deps import Base as AuditBase
from app.audit.models import ActivityLog  # noqa: F401  (registers table)
from app.notifications.deps import Base as NotificationBase
from app.notifications.models import Notification

# Identifiers used across the suite.
MANAGER_ID = "u-manager"
ADMIN_ID = "u-admin"
AUDITOR_A = "u-auditor-a"
AUDITOR_B = "u-auditor-b"
STRANGER_ID = "u-stranger"

ASSET_1 = "a-1"
ASSET_2 = "a-2"
ASSET_3 = "a-3"


def principal(user_id: str, role: Role = Role.EMPLOYEE) -> Principal:
    return Principal(id=user_id, role=role)


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #
@pytest.fixture()
def engine():
    eng = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(bind=eng)
    AuditBase.metadata.create_all(bind=eng)
    NotificationBase.metadata.create_all(bind=eng)
    # Stand-in for the Asset module's table (foundation-owned in production).
    with eng.begin() as conn:
        conn.execute(
            text(
                "CREATE TABLE assets ("
                "id VARCHAR PRIMARY KEY, "
                "name VARCHAR NOT NULL, "
                "status VARCHAR NOT NULL)"
            )
        )
        for asset_id, name in ((ASSET_1, "Laptop"), (ASSET_2, "Monitor"),
                               (ASSET_3, "Printer")):
            conn.execute(
                text("INSERT INTO assets (id, name, status) VALUES (:id, :n, :s)"),
                {"id": asset_id, "n": name, "s": "available"},
            )
    try:
        yield eng
    finally:
        NotificationBase.metadata.drop_all(bind=eng)
        AuditBase.metadata.drop_all(bind=eng)
        Base.metadata.drop_all(bind=eng)
        eng.dispose()


@pytest.fixture()
def session_factory(engine):
    return sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)


@pytest.fixture()
def db(session_factory) -> Iterator[Session]:
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def manager() -> Principal:
    return principal(MANAGER_ID, Role.ASSET_MANAGER)


@pytest.fixture()
def admin() -> Principal:
    return principal(ADMIN_ID, Role.ADMIN)


@pytest.fixture()
def auditor_a() -> Principal:
    return principal(AUDITOR_A, Role.EMPLOYEE)


@pytest.fixture()
def auditor_b() -> Principal:
    return principal(AUDITOR_B, Role.EMPLOYEE)


def asset_status(db: Session, asset_id: str) -> str:
    return db.execute(
        text("SELECT status FROM assets WHERE id = :id"), {"id": asset_id}
    ).scalar_one()


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _create_cycle(db, principal_, name="Q3 Estate Audit"):
    return svc.create_cycle(
        db,
        principal_,
        AuditCycleCreate(
            name=name,
            department_id="d-ops",
            location="HQ / Floor 2",
            start_date=date(2026, 7, 1),
            end_date=date(2026, 7, 31),
        ),
    )


def _add_item(db, principal_, cycle_id, asset_id=ASSET_1, auditor_id=AUDITOR_A):
    return svc.add_item(
        db,
        principal_,
        AuditItemCreate(
            audit_cycle_id=cycle_id, asset_id=asset_id, auditor_id=auditor_id
        ),
    )


def _verify(db, principal_, item_id, status_, remarks=None):
    return svc.verify_item(
        db, principal_, item_id, AuditItemVerify(status=status_, remarks=remarks)
    )


# --------------------------------------------------------------------------- #
# create cycle
# --------------------------------------------------------------------------- #
def test_create_cycle_starts_created(db, manager):
    cycle = _create_cycle(db, manager)
    assert cycle.id is not None
    assert cycle.status == AuditCycleStatus.CREATED
    assert cycle.created_by == manager.id
    assert cycle.started_at is None and cycle.closed_at is None


def test_create_cycle_rejects_reversed_dates(db, manager):
    with pytest.raises(ValidationError) as exc:
        svc.create_cycle(
            db,
            manager,
            AuditCycleCreate(
                name="Bad window",
                start_date=date(2026, 8, 1),
                end_date=date(2026, 7, 1),
            ),
        )
    assert "start_date" in str(exc.value)


# --------------------------------------------------------------------------- #
# enroll assets / assign auditors + duplicate rules
# --------------------------------------------------------------------------- #
def test_add_item_enrolls_asset_and_assigns_auditor(db, manager):
    cycle = _create_cycle(db, manager)
    item = _add_item(db, manager, cycle.id)
    assert item.id is not None
    assert item.audit_cycle_id == cycle.id
    assert item.asset_id == ASSET_1
    assert item.auditor_id == AUDITOR_A
    assert item.status is None
    assert item.verified_at is None


def test_add_item_unknown_asset_is_not_found(db, manager):
    cycle = _create_cycle(db, manager)
    with pytest.raises(NotFoundError):
        _add_item(db, manager, cycle.id, asset_id="does-not-exist")


def test_cannot_duplicate_asset_in_cycle(db, manager):
    cycle = _create_cycle(db, manager)
    _add_item(db, manager, cycle.id, asset_id=ASSET_1, auditor_id=AUDITOR_A)
    # Same asset, different auditor -> "already enrolled".
    with pytest.raises(ValidationError) as exc:
        _add_item(db, manager, cycle.id, asset_id=ASSET_1, auditor_id=AUDITOR_B)
    assert "already enrolled" in str(exc.value)


def test_cannot_duplicate_auditor_entry(db, manager):
    cycle = _create_cycle(db, manager)
    _add_item(db, manager, cycle.id, asset_id=ASSET_1, auditor_id=AUDITOR_A)
    # Same asset AND same auditor -> "already assigned".
    with pytest.raises(ValidationError) as exc:
        _add_item(db, manager, cycle.id, asset_id=ASSET_1, auditor_id=AUDITOR_A)
    assert "already assigned" in str(exc.value)


def test_same_asset_may_appear_in_different_cycles(db, manager):
    c1 = _create_cycle(db, manager, name="Cycle 1")
    c2 = _create_cycle(db, manager, name="Cycle 2")
    _add_item(db, manager, c1.id, asset_id=ASSET_1)
    # Not a duplicate: different cycle.
    item2 = _add_item(db, manager, c2.id, asset_id=ASSET_1)
    assert item2.audit_cycle_id == c2.id


# --------------------------------------------------------------------------- #
# start
# --------------------------------------------------------------------------- #
def test_start_moves_to_active(db, manager):
    cycle = _create_cycle(db, manager)
    _add_item(db, manager, cycle.id)
    started = svc.start_cycle(db, manager, cycle.id)
    assert started.status == AuditCycleStatus.ACTIVE
    assert started.started_at is not None


def test_cannot_start_twice(db, manager):
    cycle = _create_cycle(db, manager)
    _add_item(db, manager, cycle.id)
    svc.start_cycle(db, manager, cycle.id)
    with pytest.raises(ValidationError) as exc:
        svc.start_cycle(db, manager, cycle.id)
    assert "already been started" in str(exc.value)


def test_start_notifies_assigned_auditors(db, manager):
    cycle = _create_cycle(db, manager)
    _add_item(db, manager, cycle.id, asset_id=ASSET_1, auditor_id=AUDITOR_A)
    _add_item(db, manager, cycle.id, asset_id=ASSET_2, auditor_id=AUDITOR_B)
    svc.start_cycle(db, manager, cycle.id)

    started_notifs = db.execute(
        select(func.count())
        .select_from(Notification)
        .where(Notification.title == "Audit started")
    ).scalar_one()
    assert started_notifs == 2


# --------------------------------------------------------------------------- #
# verify + cannot-verify-twice rule
# --------------------------------------------------------------------------- #
def test_verify_marks_status(db, manager, auditor_a):
    cycle = _create_cycle(db, manager)
    item = _add_item(db, manager, cycle.id, auditor_id=AUDITOR_A)
    svc.start_cycle(db, manager, cycle.id)

    verified = _verify(db, auditor_a, item.id, AuditItemStatus.VERIFIED, "OK")
    assert verified.status == AuditItemStatus.VERIFIED
    assert verified.remarks == "OK"
    assert verified.verified_at is not None


def test_cannot_verify_before_start(db, manager, auditor_a):
    cycle = _create_cycle(db, manager)
    item = _add_item(db, manager, cycle.id, auditor_id=AUDITOR_A)
    with pytest.raises(ValidationError) as exc:
        _verify(db, auditor_a, item.id, AuditItemStatus.VERIFIED)
    assert "started" in str(exc.value).lower()


def test_cannot_verify_twice(db, manager, auditor_a):
    cycle = _create_cycle(db, manager)
    item = _add_item(db, manager, cycle.id, auditor_id=AUDITOR_A)
    svc.start_cycle(db, manager, cycle.id)
    _verify(db, auditor_a, item.id, AuditItemStatus.VERIFIED)
    with pytest.raises(ValidationError) as exc:
        _verify(db, auditor_a, item.id, AuditItemStatus.DAMAGED)
    assert "already been verified" in str(exc.value)


def test_only_assigned_auditor_can_verify(db, manager, auditor_a, auditor_b):
    cycle = _create_cycle(db, manager)
    item = _add_item(db, manager, cycle.id, auditor_id=AUDITOR_A)
    svc.start_cycle(db, manager, cycle.id)
    with pytest.raises(PermissionDeniedError):
        _verify(db, auditor_b, item.id, AuditItemStatus.VERIFIED)
    # The assigned auditor succeeds.
    assert _verify(db, auditor_a, item.id, AuditItemStatus.VERIFIED).id == item.id


def test_admin_may_verify_any_item(db, manager, admin):
    cycle = _create_cycle(db, manager)
    item = _add_item(db, manager, cycle.id, auditor_id=AUDITOR_A)
    svc.start_cycle(db, manager, cycle.id)
    verified = _verify(db, admin, item.id, AuditItemStatus.VERIFIED)
    assert verified.status == AuditItemStatus.VERIFIED


def test_discrepancy_notifies_owner(db, manager, auditor_a):
    cycle = _create_cycle(db, manager)
    item = _add_item(db, manager, cycle.id, auditor_id=AUDITOR_A)
    svc.start_cycle(db, manager, cycle.id)
    _verify(db, auditor_a, item.id, AuditItemStatus.DAMAGED, "cracked screen")

    alerts = db.execute(
        select(func.count())
        .select_from(Notification)
        .where(
            Notification.recipient_id == MANAGER_ID,
            Notification.title == "Audit discrepancy found",
        )
    ).scalar_one()
    assert alerts == 1


# --------------------------------------------------------------------------- #
# close + empty/lock rules + Lost transition
# --------------------------------------------------------------------------- #
def test_cannot_close_empty_audit(db, manager):
    cycle = _create_cycle(db, manager)
    svc.start_cycle(db, manager, cycle.id)
    with pytest.raises(ValidationError) as exc:
        svc.close_cycle(db, manager, cycle.id)
    assert "empty audit" in str(exc.value).lower()


def test_cannot_close_before_start(db, manager):
    cycle = _create_cycle(db, manager)
    _add_item(db, manager, cycle.id)
    with pytest.raises(ValidationError) as exc:
        svc.close_cycle(db, manager, cycle.id)
    assert "started" in str(exc.value).lower()


def test_close_marks_missing_assets_lost(db, manager, auditor_a):
    cycle = _create_cycle(db, manager)
    i1 = _add_item(db, manager, cycle.id, asset_id=ASSET_1, auditor_id=AUDITOR_A)
    i2 = _add_item(db, manager, cycle.id, asset_id=ASSET_2, auditor_id=AUDITOR_A)
    i3 = _add_item(db, manager, cycle.id, asset_id=ASSET_3, auditor_id=AUDITOR_A)
    svc.start_cycle(db, manager, cycle.id)

    _verify(db, auditor_a, i1.id, AuditItemStatus.VERIFIED)
    _verify(db, auditor_a, i2.id, AuditItemStatus.MISSING)
    _verify(db, auditor_a, i3.id, AuditItemStatus.DAMAGED)

    assert asset_status(db, ASSET_2) == "available"  # not yet
    closed = svc.close_cycle(db, manager, cycle.id)
    assert closed.status == AuditCycleStatus.CLOSED
    assert closed.closed_at is not None

    # Only the confirmed-missing asset becomes LOST (via AssetGateway).
    assert asset_status(db, ASSET_2) == "lost"
    assert asset_status(db, ASSET_1) == "available"
    assert asset_status(db, ASSET_3) == "available"  # damaged != lost


def test_close_does_not_duplicate_close_notification(db, manager, auditor_a):
    # The cycle creator is also enrolled as an auditor: the recipient set must
    # dedup so they receive exactly one "Audit closed" message, not two.
    cycle = _create_cycle(db, manager)
    i1 = _add_item(db, manager, cycle.id, asset_id=ASSET_1, auditor_id=MANAGER_ID)
    i2 = _add_item(db, manager, cycle.id, asset_id=ASSET_2, auditor_id=AUDITOR_A)
    svc.start_cycle(db, manager, cycle.id)
    _verify(db, manager, i1.id, AuditItemStatus.VERIFIED)
    _verify(db, auditor_a, i2.id, AuditItemStatus.VERIFIED)
    svc.close_cycle(db, manager, cycle.id)

    closed_msgs = db.execute(
        select(func.count())
        .select_from(Notification)
        .where(
            Notification.recipient_id == MANAGER_ID,
            Notification.title == "Audit closed",
        )
    ).scalar_one()
    assert closed_msgs == 1


def test_closed_audit_is_locked_for_cycle_edits(db, manager, auditor_a):
    cycle = _create_cycle(db, manager)
    item = _add_item(db, manager, cycle.id, auditor_id=AUDITOR_A)
    svc.start_cycle(db, manager, cycle.id)
    _verify(db, auditor_a, item.id, AuditItemStatus.VERIFIED)
    svc.close_cycle(db, manager, cycle.id)

    with pytest.raises(ValidationError) as exc:
        svc.update_cycle(db, manager, cycle.id, AuditCycleUpdate(name="rename"))
    assert "closed audit" in str(exc.value).lower()


def test_closed_audit_is_locked_for_item_edits(db, manager, auditor_a):
    cycle = _create_cycle(db, manager)
    i1 = _add_item(db, manager, cycle.id, asset_id=ASSET_1, auditor_id=AUDITOR_A)
    i2 = _add_item(db, manager, cycle.id, asset_id=ASSET_2, auditor_id=AUDITOR_A)
    svc.start_cycle(db, manager, cycle.id)
    _verify(db, auditor_a, i1.id, AuditItemStatus.VERIFIED)
    svc.close_cycle(db, manager, cycle.id)

    # Cannot verify a leftover item after close.
    with pytest.raises(ValidationError) as exc:
        _verify(db, auditor_a, i2.id, AuditItemStatus.VERIFIED)
    assert "closed audit" in str(exc.value).lower()


def test_cannot_add_item_to_closed_audit(db, manager, auditor_a):
    cycle = _create_cycle(db, manager)
    item = _add_item(db, manager, cycle.id, asset_id=ASSET_1, auditor_id=AUDITOR_A)
    svc.start_cycle(db, manager, cycle.id)
    _verify(db, auditor_a, item.id, AuditItemStatus.VERIFIED)
    svc.close_cycle(db, manager, cycle.id)
    with pytest.raises(ValidationError) as exc:
        _add_item(db, manager, cycle.id, asset_id=ASSET_2)
    assert "closed audit" in str(exc.value).lower()


def test_cannot_close_twice(db, manager, auditor_a):
    cycle = _create_cycle(db, manager)
    item = _add_item(db, manager, cycle.id, auditor_id=AUDITOR_A)
    svc.start_cycle(db, manager, cycle.id)
    _verify(db, auditor_a, item.id, AuditItemStatus.VERIFIED)
    svc.close_cycle(db, manager, cycle.id)
    with pytest.raises(ValidationError) as exc:
        svc.close_cycle(db, manager, cycle.id)
    assert "already closed" in str(exc.value)


# --------------------------------------------------------------------------- #
# discrepancy report
# --------------------------------------------------------------------------- #
def test_report_counts_and_buckets(db, manager, auditor_a):
    cycle = _create_cycle(db, manager)
    i1 = _add_item(db, manager, cycle.id, asset_id=ASSET_1, auditor_id=AUDITOR_A)
    i2 = _add_item(db, manager, cycle.id, asset_id=ASSET_2, auditor_id=AUDITOR_A)
    i3 = _add_item(db, manager, cycle.id, asset_id=ASSET_3, auditor_id=AUDITOR_A)
    svc.start_cycle(db, manager, cycle.id)
    _verify(db, auditor_a, i1.id, AuditItemStatus.VERIFIED)
    _verify(db, auditor_a, i2.id, AuditItemStatus.MISSING)
    # i3 left unverified (pending).

    report = svc.generate_report(db, manager, cycle.id)
    assert report.summary.total_items == 3
    assert report.summary.verified == 1
    assert report.summary.missing == 1
    assert report.summary.damaged == 0
    assert report.summary.pending == 1
    assert report.discrepancy_count == 1
    assert [i.asset_id for i in report.verified_assets] == [ASSET_1]
    assert [i.asset_id for i in report.missing_assets] == [ASSET_2]


# --------------------------------------------------------------------------- #
# visibility / access control
# --------------------------------------------------------------------------- #
def test_stranger_cannot_view_cycle(db, manager):
    cycle = _create_cycle(db, manager)
    _add_item(db, manager, cycle.id, auditor_id=AUDITOR_A)
    stranger = principal(STRANGER_ID, Role.EMPLOYEE)
    with pytest.raises(PermissionDeniedError):
        svc.get_cycle(db, stranger, cycle.id)
    # An assigned auditor may view it.
    assert svc.get_cycle(db, principal(AUDITOR_A), cycle.id).id == cycle.id


def test_list_cycles_scoped_for_non_manager(db, manager):
    c1 = _create_cycle(db, manager, name="C1")
    _create_cycle(db, manager, name="C2")
    _add_item(db, manager, c1.id, auditor_id=AUDITOR_A)

    mine, total = svc.list_cycles(db, principal(AUDITOR_A))
    assert total == 1 and mine[0].id == c1.id
    # Manager sees both.
    _, total_all = svc.list_cycles(db, manager)
    assert total_all == 2


# --------------------------------------------------------------------------- #
# activity log integration
# --------------------------------------------------------------------------- #
def test_actions_write_activity_log(db, manager, auditor_a):
    cycle = _create_cycle(db, manager)
    item = _add_item(db, manager, cycle.id, auditor_id=AUDITOR_A)
    svc.start_cycle(db, manager, cycle.id)
    _verify(db, auditor_a, item.id, AuditItemStatus.VERIFIED)
    svc.close_cycle(db, manager, cycle.id)

    actions = set(
        db.execute(
            select(ActivityLog.action).where(
                ActivityLog.entity_type.in_(("audit_cycle", "audit_item"))
            )
        )
        .scalars()
        .all()
    )
    assert {"created", "auditor_assigned", "started", "verified", "closed"} <= actions


# --------------------------------------------------------------------------- #
# API-level tests (thin router + dependency wiring)
# --------------------------------------------------------------------------- #
class _Holder:
    def __init__(self) -> None:
        self.current = principal(MANAGER_ID, Role.ASSET_MANAGER)


@pytest.fixture()
def client(session_factory) -> Iterator[TestClient]:
    app = FastAPI()
    register_routes(app)

    holder = _Holder()

    def override_get_db() -> Iterator[Session]:
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    def override_get_current_user() -> Principal:
        return holder.current

    app.dependency_overrides[deps.get_db] = override_get_db
    app.dependency_overrides[deps.get_current_user] = override_get_current_user

    test_client = TestClient(app)
    test_client.as_user = holder  # type: ignore[attr-defined]
    yield test_client


def _api_create_cycle(client):
    return client.post(
        "/api/asset-audit/cycle",
        json={
            "name": "API Audit",
            "department_id": "d-ops",
            "location": "HQ",
            "start_date": "2026-07-01",
            "end_date": "2026-07-31",
        },
    )


def test_api_full_lifecycle(client):
    client.as_user.current = principal(MANAGER_ID, Role.ASSET_MANAGER)
    resp = _api_create_cycle(client)
    assert resp.status_code == 201
    cycle_id = resp.json()["id"]
    assert resp.json()["status"] == "created"

    # Enroll two assets.
    for asset_id in (ASSET_1, ASSET_2):
        item = client.post(
            "/api/asset-audit/item",
            json={
                "audit_cycle_id": cycle_id,
                "asset_id": asset_id,
                "auditor_id": AUDITOR_A,
            },
        )
        assert item.status_code == 201

    assert client.post(f"/api/asset-audit/cycle/{cycle_id}/start").status_code == 200

    # The assigned auditor verifies both (one missing).
    client.as_user.current = principal(AUDITOR_A, Role.EMPLOYEE)
    items = client.get(f"/api/asset-audit/cycle/{cycle_id}/items").json()
    id_by_asset = {i["asset_id"]: i["id"] for i in items}
    assert (
        client.put(
            f"/api/asset-audit/item/{id_by_asset[ASSET_1]}",
            json={"status": "verified"},
        ).status_code
        == 200
    )
    assert (
        client.put(
            f"/api/asset-audit/item/{id_by_asset[ASSET_2]}",
            json={"status": "missing", "remarks": "not on shelf"},
        ).status_code
        == 200
    )

    # Report reflects the discrepancy.
    client.as_user.current = principal(MANAGER_ID, Role.ASSET_MANAGER)
    report = client.get(f"/api/asset-audit/report/{cycle_id}").json()
    assert report["discrepancy_count"] == 1
    assert report["summary"]["missing"] == 1

    close = client.post(f"/api/asset-audit/cycle/{cycle_id}/close")
    assert close.status_code == 200
    assert close.json()["status"] == "closed"


def test_api_create_requires_manager(client):
    client.as_user.current = principal(AUDITOR_A, Role.EMPLOYEE)
    resp = _api_create_cycle(client)
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "permission_denied"


def test_api_close_empty_audit_is_400(client):
    client.as_user.current = principal(MANAGER_ID, Role.ASSET_MANAGER)
    cycle_id = _api_create_cycle(client).json()["id"]
    assert client.post(f"/api/asset-audit/cycle/{cycle_id}/start").status_code == 200
    resp = client.post(f"/api/asset-audit/cycle/{cycle_id}/close")
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "validation_error"


def test_api_duplicate_asset_is_400(client):
    client.as_user.current = principal(MANAGER_ID, Role.ASSET_MANAGER)
    cycle_id = _api_create_cycle(client).json()["id"]
    body = {"audit_cycle_id": cycle_id, "asset_id": ASSET_1, "auditor_id": AUDITOR_A}
    assert client.post("/api/asset-audit/item", json=body).status_code == 201
    dup = client.post("/api/asset-audit/item", json=body)
    assert dup.status_code == 400
    assert "already assigned" in dup.json()["error"]["message"]


def test_api_get_missing_cycle_is_404(client):
    client.as_user.current = principal(MANAGER_ID, Role.ASSET_MANAGER)
    assert client.get("/api/asset-audit/cycle/999999").status_code == 404
