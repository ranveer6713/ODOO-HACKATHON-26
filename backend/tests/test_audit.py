"""Unit and API tests for the Audit (activity-log) module.

Exercised in isolation: an in-memory SQLite database holds the module-owned
``activity_logs`` table plus the sibling ``notifications`` table (flagging alerts
the actor through the shared NotificationService). Foundation dependencies are
overridden.
"""
from __future__ import annotations

from typing import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.audit import deps, register_routes
from app.audit.deps import Base, Principal, Role
from app.audit.exceptions import PermissionDeniedError, ValidationError
from app.audit.models import ActivityLog, AuditSeverity  # noqa: F401
from app.audit.service import audit_service as svc
from app.notifications.deps import Base as NotificationBase
from app.notifications.models import Notification

ACTOR = "u-actor"
MANAGER = "u-manager"


def principal(user_id: str, role: Role = Role.EMPLOYEE) -> Principal:
    return Principal(id=user_id, role=role)


@pytest.fixture()
def engine():
    eng = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(bind=eng)
    NotificationBase.metadata.create_all(bind=eng)
    try:
        yield eng
    finally:
        NotificationBase.metadata.drop_all(bind=eng)
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


def _record(db, actor=ACTOR, action="created", entity_id="1"):
    entry = svc.record(
        db,
        actor_id=actor,
        action=action,
        entity_type="maintenance_request",
        entity_id=entity_id,
        description="something happened",
    )
    db.commit()
    return entry


# --------------------------------------------------------------------------- #
# record (append-only logging port)
# --------------------------------------------------------------------------- #
def test_record_appends_entry(db):
    entry = _record(db)
    assert entry.id is not None
    assert entry.severity == AuditSeverity.INFO
    assert entry.flagged is False


def test_record_requires_all_identity_fields(db):
    with pytest.raises(ValidationError):
        svc.record(
            db, actor_id="", action="x", entity_type="y", entity_id="1"
        )


def test_record_coerces_severity_string(db):
    entry = svc.record(
        db,
        actor_id=ACTOR,
        action="deleted",
        entity_type="booking",
        entity_id="7",
        severity="warning",
    )
    db.commit()
    assert entry.severity == AuditSeverity.WARNING


# --------------------------------------------------------------------------- #
# reads / scoping
# --------------------------------------------------------------------------- #
def test_non_manager_sees_only_own_entries(db):
    _record(db, actor=ACTOR)
    _record(db, actor="someone-else")

    mine, total = svc.list(db, principal(ACTOR))
    assert total == 1
    assert all(e.actor_id == ACTOR for e in mine)

    _, manager_total = svc.list(db, principal(MANAGER, Role.ASSET_MANAGER))
    assert manager_total == 2


def test_non_manager_cannot_view_others_entry(db):
    entry = _record(db, actor=ACTOR)
    with pytest.raises(PermissionDeniedError):
        svc.get(db, principal("stranger"), entry.id)


# --------------------------------------------------------------------------- #
# flag / acknowledge review lifecycle
# --------------------------------------------------------------------------- #
def test_flag_notifies_actor_and_records_meta_entry(db):
    entry = _record(db, actor=ACTOR)
    before = db.execute(select(func.count()).select_from(ActivityLog)).scalar_one()

    flagged = svc.flag(db, principal(MANAGER, Role.ASSET_MANAGER), entry.id, "looks off")
    assert flagged.flagged is True
    assert flagged.flagged_by == MANAGER
    assert flagged.flag_reason == "looks off"

    # The actor received a notification.
    notif = db.execute(
        select(Notification).where(Notification.recipient_id == ACTOR)
    ).scalars().all()
    assert len(notif) == 1
    assert "flagged" in notif[0].message.lower()

    # Flagging is itself recorded to the trail (a new meta entry).
    after = db.execute(select(func.count()).select_from(ActivityLog)).scalar_one()
    assert after == before + 1


def test_employee_cannot_flag(db):
    entry = _record(db, actor=ACTOR)
    with pytest.raises(PermissionDeniedError):
        svc.flag(db, principal("someone"), entry.id, "no rights")


def test_cannot_flag_twice(db):
    entry = _record(db, actor=ACTOR)
    mgr = principal(MANAGER, Role.ASSET_MANAGER)
    svc.flag(db, mgr, entry.id, "first")
    with pytest.raises(ValidationError):
        svc.flag(db, mgr, entry.id, "again")


def test_acknowledge_requires_flag_first(db):
    entry = _record(db, actor=ACTOR)
    with pytest.raises(ValidationError):
        svc.acknowledge(db, principal(ACTOR), entry.id)


def test_actor_can_acknowledge_flag(db):
    entry = _record(db, actor=ACTOR)
    svc.flag(db, principal(MANAGER, Role.ASSET_MANAGER), entry.id, "check this")
    acked = svc.acknowledge(db, principal(ACTOR), entry.id)
    assert acked.acknowledged is True
    assert acked.acknowledged_by == ACTOR


def test_stranger_cannot_acknowledge(db):
    entry = _record(db, actor=ACTOR)
    svc.flag(db, principal(MANAGER, Role.ASSET_MANAGER), entry.id, "check")
    with pytest.raises(PermissionDeniedError):
        svc.acknowledge(db, principal("stranger"), entry.id)


# --------------------------------------------------------------------------- #
# API
# --------------------------------------------------------------------------- #
class _Holder:
    def __init__(self) -> None:
        self.current = principal(MANAGER, Role.ASSET_MANAGER)


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

    app.dependency_overrides[deps.get_db] = override_get_db
    app.dependency_overrides[deps.get_current_user] = lambda: holder.current
    test_client = TestClient(app)
    test_client.as_user = holder  # type: ignore[attr-defined]
    yield test_client


def test_api_list_and_flag(client, session_factory):
    session = session_factory()
    entry = svc.record(
        session,
        actor_id=ACTOR,
        action="approved",
        entity_type="booking",
        entity_id="3",
    )
    session.commit()
    entry_id = entry.id
    session.close()

    listing = client.get("/api/audit")
    assert listing.status_code == 200
    assert listing.json()["meta"]["total"] >= 1

    flagged = client.post(
        f"/api/audit/{entry_id}/flag", json={"reason": "audit needed"}
    )
    assert flagged.status_code == 200
    assert flagged.json()["flagged"] is True


def test_api_employee_cannot_flag(client, session_factory):
    session = session_factory()
    entry = svc.record(
        session, actor_id=ACTOR, action="created", entity_type="booking", entity_id="9"
    )
    session.commit()
    entry_id = entry.id
    session.close()

    client.as_user.current = principal("emp", Role.EMPLOYEE)
    resp = client.post(f"/api/audit/{entry_id}/flag", json={"reason": "x"})
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "permission_denied"
