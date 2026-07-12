"""Unit and API tests for the Booking module.

Covers the full state machine and every business rule:
    * A valid, future time window
    * No double-booking of an asset for overlapping periods
    * Unavailable assets (under maintenance / disposed) cannot be booked
    * Cannot approve twice / check out before approval / check in before checkout
    * Cancellation only before check-out; edit only while pending
    * Asset interaction happens through AssetGateway (checkout -> booked,
      checkin -> available)
    * Every workflow action creates an activity-log entry and notifies the
      requester
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.audit.deps import Base as AuditBase
from app.audit.models import ActivityLog
from app.booking import deps, register_routes
from app.booking.deps import Base, Principal, Role
from app.booking.exceptions import (
    ConflictError,
    NotFoundError,
    PermissionDeniedError,
    ValidationError,
)
from app.booking.models import Booking, BookingStatus  # noqa: F401
from app.booking.schemas import BookingCreate, BookingUpdate
from app.booking.service import booking_service as svc
from app.notifications.deps import Base as NotificationBase
from app.notifications.models import Notification

EMPLOYEE_ID = "u-employee"
OTHER_ID = "u-other"
MANAGER_ID = "u-manager"

ASSET_OK = "a-100"
ASSET_MAINT = "a-maint"
ASSET_DISPOSED = "a-disposed"


def principal(user_id: str, role: Role = Role.EMPLOYEE) -> Principal:
    return Principal(id=user_id, role=role)


def _window(offset_hours: int = 1, length_hours: int = 2):
    start = datetime.now(timezone.utc) + timedelta(hours=offset_hours)
    return start, start + timedelta(hours=length_hours)


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
    with eng.begin() as conn:
        conn.execute(
            text(
                "CREATE TABLE assets ("
                "id VARCHAR PRIMARY KEY, "
                "name VARCHAR NOT NULL, "
                "status VARCHAR NOT NULL)"
            )
        )
        for aid, name, status in (
            (ASSET_OK, "Projector", "available"),
            (ASSET_MAINT, "Drill", "under_maintenance"),
            (ASSET_DISPOSED, "Old Laptop", "disposed"),
        ):
            conn.execute(
                text("INSERT INTO assets (id, name, status) VALUES (:i, :n, :s)"),
                {"i": aid, "n": name, "s": status},
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
def employee() -> Principal:
    return principal(EMPLOYEE_ID)


@pytest.fixture()
def manager() -> Principal:
    return principal(MANAGER_ID, Role.ASSET_MANAGER)


def asset_status(db: Session, asset_id: str) -> str:
    return db.execute(
        text("SELECT status FROM assets WHERE id = :id"), {"id": asset_id}
    ).scalar_one()


def _create(db, actor, asset_id=ASSET_OK, offset_hours=1, length_hours=2):
    start, end = _window(offset_hours, length_hours)
    return svc.create(
        db,
        actor,
        BookingCreate(
            asset_id=asset_id,
            purpose="Team demo",
            start_time=start,
            end_time=end,
        ),
    )


def _drive_to_checked_out(db, employee, manager):
    booking = _create(db, employee)
    svc.approve(db, manager, booking.id)
    return svc.check_out(db, employee, booking.id)


# --------------------------------------------------------------------------- #
# create / asset + window + overlap rules
# --------------------------------------------------------------------------- #
def test_create_starts_pending(db, employee):
    booking = _create(db, employee)
    assert booking.id is not None
    assert booking.status == BookingStatus.PENDING
    assert booking.requested_by == employee.id


def test_disposed_asset_cannot_be_booked(db, employee):
    with pytest.raises(ValidationError) as exc:
        _create(db, employee, asset_id=ASSET_DISPOSED)
    assert "disposed" in str(exc.value).lower()


def test_under_maintenance_asset_cannot_be_booked(db, employee):
    with pytest.raises(ValidationError):
        _create(db, employee, asset_id=ASSET_MAINT)


def test_unknown_asset_is_not_found(db, employee):
    with pytest.raises(NotFoundError):
        _create(db, employee, asset_id="ghost")


def test_end_before_start_is_rejected():
    start, _ = _window()
    with pytest.raises(Exception):
        BookingCreate(
            asset_id=ASSET_OK,
            purpose="bad",
            start_time=start,
            end_time=start - timedelta(hours=1),
        )


def test_past_window_is_rejected(db, employee):
    start = datetime.now(timezone.utc) - timedelta(hours=3)
    end = datetime.now(timezone.utc) - timedelta(hours=1)
    with pytest.raises(ValidationError):
        svc.create(
            db,
            employee,
            BookingCreate(
                asset_id=ASSET_OK, purpose="late", start_time=start, end_time=end
            ),
        )


def test_overlapping_booking_conflicts(db, employee):
    _create(db, employee, offset_hours=2, length_hours=2)  # 2h..4h
    with pytest.raises(ConflictError):
        _create(db, employee, offset_hours=3, length_hours=2)  # 3h..5h overlaps


def test_adjacent_booking_is_allowed(db, employee):
    _create(db, employee, offset_hours=2, length_hours=1)  # 2h..3h
    # 3h..4h touches but does not overlap.
    ok = _create(db, employee, offset_hours=3, length_hours=1)
    assert ok.status == BookingStatus.PENDING


# --------------------------------------------------------------------------- #
# approve / reject
# --------------------------------------------------------------------------- #
def test_approve_moves_to_approved(db, employee, manager):
    booking = _create(db, employee)
    approved = svc.approve(db, manager, booking.id)
    assert approved.status == BookingStatus.APPROVED
    assert approved.approved_by == manager.id
    # Approval alone does not take the asset off the shelf.
    assert asset_status(db, ASSET_OK) == "available"


def test_cannot_approve_twice(db, employee, manager):
    booking = _create(db, employee)
    svc.approve(db, manager, booking.id)
    with pytest.raises(ValidationError) as exc:
        svc.approve(db, manager, booking.id)
    assert "already been approved" in str(exc.value)


def test_reject_pending_booking(db, employee, manager):
    booking = _create(db, employee)
    rejected = svc.reject(db, manager, booking.id, "No budget")
    assert rejected.status == BookingStatus.REJECTED
    assert rejected.rejection_reason == "No budget"


def test_cannot_reject_after_approval(db, employee, manager):
    booking = _create(db, employee)
    svc.approve(db, manager, booking.id)
    with pytest.raises(ValidationError):
        svc.reject(db, manager, booking.id, "too late")


# --------------------------------------------------------------------------- #
# checkout / checkin + asset gateway interaction
# --------------------------------------------------------------------------- #
def test_cannot_check_out_before_approval(db, employee):
    booking = _create(db, employee)
    with pytest.raises(ValidationError):
        svc.check_out(db, employee, booking.id)


def test_check_out_marks_asset_booked(db, employee, manager):
    booking = _create(db, employee)
    svc.approve(db, manager, booking.id)
    out = svc.check_out(db, employee, booking.id)
    assert out.status == BookingStatus.CHECKED_OUT
    assert out.checked_out_at is not None
    assert asset_status(db, ASSET_OK) == "booked"


def test_check_in_returns_asset_available(db, employee, manager):
    booking = _drive_to_checked_out(db, employee, manager)
    assert asset_status(db, ASSET_OK) == "booked"
    done = svc.check_in(db, employee, booking.id)
    assert done.status == BookingStatus.CHECKED_IN
    assert asset_status(db, ASSET_OK) == "available"


def test_cannot_check_in_before_checkout(db, employee, manager):
    booking = _create(db, employee)
    svc.approve(db, manager, booking.id)
    with pytest.raises(ValidationError):
        svc.check_in(db, employee, booking.id)


# --------------------------------------------------------------------------- #
# cancel / edit rules
# --------------------------------------------------------------------------- #
def test_cancel_pending_booking(db, employee):
    booking = _create(db, employee)
    cancelled = svc.cancel(db, employee, booking.id, "changed plans")
    assert cancelled.status == BookingStatus.CANCELLED
    assert cancelled.cancellation_reason == "changed plans"


def test_cannot_cancel_after_checkout(db, employee, manager):
    booking = _drive_to_checked_out(db, employee, manager)
    with pytest.raises(ValidationError):
        svc.cancel(db, employee, booking.id)


def test_cannot_cancel_twice(db, employee):
    booking = _create(db, employee)
    svc.cancel(db, employee, booking.id, "changed plans")
    # An already-cancelled booking is a terminal state; cancelling again is illegal.
    with pytest.raises(ValidationError):
        svc.cancel(db, employee, booking.id)


def test_cancelled_window_frees_the_slot(db, employee):
    first = _create(db, employee, offset_hours=2, length_hours=2)
    svc.cancel(db, employee, first.id)
    # Same window is now free because the cancelled booking no longer counts.
    ok = _create(db, employee, offset_hours=2, length_hours=2)
    assert ok.status == BookingStatus.PENDING


def test_edit_only_while_pending(db, employee, manager):
    booking = _create(db, employee)
    updated = svc.update(
        db, employee, booking.id, BookingUpdate(purpose="Updated purpose")
    )
    assert updated.purpose == "Updated purpose"

    svc.approve(db, manager, booking.id)
    with pytest.raises(ValidationError):
        svc.update(db, employee, booking.id, BookingUpdate(purpose="too late"))


def test_edit_to_conflicting_window_is_rejected(db, employee):
    _create(db, employee, offset_hours=2, length_hours=2)  # 2h..4h
    movable = _create(db, employee, offset_hours=6, length_hours=1)  # 6h..7h
    start = datetime.now(timezone.utc) + timedelta(hours=3)
    with pytest.raises(ConflictError):
        svc.update(
            db,
            employee,
            movable.id,
            BookingUpdate(
                start_time=start, end_time=start + timedelta(hours=1)
            ),
        )


def test_non_owner_non_manager_cannot_edit(db, employee):
    booking = _create(db, employee)
    with pytest.raises(PermissionDeniedError):
        svc.update(db, principal(OTHER_ID), booking.id, BookingUpdate(purpose="x"))


# --------------------------------------------------------------------------- #
# visibility
# --------------------------------------------------------------------------- #
def test_employee_cannot_view_others_booking(db, employee, manager):
    booking = _create(db, employee)
    with pytest.raises(PermissionDeniedError):
        svc.get(db, principal(OTHER_ID), booking.id)
    assert svc.get(db, manager, booking.id).id == booking.id


def test_list_scopes_non_managers_to_their_own(db, employee, manager):
    _create(db, employee, offset_hours=2)
    _create(db, principal(OTHER_ID), offset_hours=10)

    mine, total = svc.list(db, employee)
    assert total == 1
    assert all(b.requested_by == employee.id for b in mine)

    _, manager_total = svc.list(db, manager)
    assert manager_total == 2


# --------------------------------------------------------------------------- #
# cross-cutting: audit trail + notifications
# --------------------------------------------------------------------------- #
def test_workflow_writes_audit_trail_and_notifications(db, employee, manager):
    booking = _create(db, employee)
    svc.approve(db, manager, booking.id)

    logs = db.execute(
        select(ActivityLog).where(
            ActivityLog.entity_type == "booking",
            ActivityLog.entity_id == str(booking.id),
        )
    ).scalars().all()
    actions = {log.action for log in logs}
    assert {"created", "approved"} <= actions

    # The requester was notified for both submission and approval.
    notif_count = db.execute(
        select(func.count())
        .select_from(Notification)
        .where(Notification.recipient_id == employee.id)
    ).scalar_one()
    assert notif_count >= 2


def test_full_workflow_happy_path(db, employee, manager):
    booking = _create(db, employee)
    assert svc.approve(db, manager, booking.id).status == BookingStatus.APPROVED
    assert svc.check_out(db, employee, booking.id).status == BookingStatus.CHECKED_OUT
    assert svc.check_in(db, employee, booking.id).status == BookingStatus.CHECKED_IN


# --------------------------------------------------------------------------- #
# API
# --------------------------------------------------------------------------- #
class _Holder:
    def __init__(self) -> None:
        self.current = principal(EMPLOYEE_ID)


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


def _post_create(client, asset_id=ASSET_OK, offset_hours=1):
    start = datetime.now(timezone.utc) + timedelta(hours=offset_hours)
    end = start + timedelta(hours=2)
    return client.post(
        "/api/bookings",
        json={
            "asset_id": asset_id,
            "purpose": "Workshop",
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
        },
    )


def test_api_create_returns_201(client, employee):
    client.as_user.current = employee
    resp = _post_create(client)
    assert resp.status_code == 201
    assert resp.json()["status"] == "pending"


def test_api_full_lifecycle(client, employee, manager):
    client.as_user.current = employee
    booking_id = _post_create(client).json()["id"]

    client.as_user.current = manager
    assert client.post(f"/api/bookings/{booking_id}/approve").status_code == 200

    client.as_user.current = employee
    assert client.post(f"/api/bookings/{booking_id}/checkout").status_code == 200
    checkin = client.post(f"/api/bookings/{booking_id}/checkin")
    assert checkin.status_code == 200
    assert checkin.json()["status"] == "checked_in"


def test_api_approve_requires_manager(client, employee):
    client.as_user.current = employee
    booking_id = _post_create(client).json()["id"]
    resp = client.post(f"/api/bookings/{booking_id}/approve")
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "permission_denied"


def test_api_overlap_returns_conflict(client, employee):
    client.as_user.current = employee
    assert _post_create(client, offset_hours=2).status_code == 201
    resp = _post_create(client, offset_hours=2)
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "conflict"


def test_api_disposed_asset_rejected(client, employee):
    client.as_user.current = employee
    resp = _post_create(client, asset_id=ASSET_DISPOSED)
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "validation_error"
