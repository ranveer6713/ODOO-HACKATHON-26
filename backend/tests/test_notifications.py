"""Unit and API tests for the Notifications module.

Exercised in complete isolation: an in-memory SQLite database holds the
module-owned ``notifications`` table; the foundation-owned ``get_db`` and
``get_current_user`` dependencies are overridden.
"""
from __future__ import annotations

from typing import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.notifications import deps, register_routes
from app.notifications.deps import Base, Principal, Role
from app.notifications.exceptions import NotFoundError, PermissionDeniedError
from app.notifications.models import Notification, NotificationType  # noqa: F401
from app.notifications.service import notification_service as svc

USER_A = "u-a"
USER_B = "u-b"


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
    try:
        yield eng
    finally:
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


def _deliver(db, recipient=USER_A, type=NotificationType.SYSTEM):
    notification = svc.notify(
        db,
        recipient_id=recipient,
        type=type,
        title="Hello",
        message="You have an update",
    )
    db.commit()
    return notification


# --------------------------------------------------------------------------- #
# delivery
# --------------------------------------------------------------------------- #
def test_notify_persists_unread(db):
    n = _deliver(db)
    assert n.id is not None
    assert n.recipient_id == USER_A
    assert n.is_read is False
    assert n.read_at is None


def test_notify_accepts_string_type(db):
    n = svc.notify(
        db, recipient_id=USER_A, type="booking", title="t", message="m"
    )
    db.commit()
    assert n.type == NotificationType.BOOKING


def test_notify_rejects_unknown_type(db):
    from app.notifications.exceptions import ValidationError

    with pytest.raises(ValidationError):
        svc.notify(db, recipient_id=USER_A, type="nope", title="t", message="m")


def test_notify_requires_recipient_and_content(db):
    from app.notifications.exceptions import ValidationError

    with pytest.raises(ValidationError):
        svc.notify(db, recipient_id="  ", type="system", title="t", message="m")
    with pytest.raises(ValidationError):
        svc.notify(db, recipient_id=USER_A, type="system", title="", message="m")


# --------------------------------------------------------------------------- #
# reads / scoping
# --------------------------------------------------------------------------- #
def test_list_is_scoped_to_recipient(db):
    _deliver(db, recipient=USER_A)
    _deliver(db, recipient=USER_B)

    items, total = svc.list_for(db, principal(USER_A))
    assert total == 1
    assert all(n.recipient_id == USER_A for n in items)


def test_unread_only_filter(db):
    n1 = _deliver(db, recipient=USER_A)
    _deliver(db, recipient=USER_A)
    svc.mark_read(db, principal(USER_A), n1.id)

    _, total_all = svc.list_for(db, principal(USER_A))
    _, total_unread = svc.list_for(db, principal(USER_A), unread_only=True)
    assert total_all == 2
    assert total_unread == 1


def test_cannot_read_others_notification(db):
    n = _deliver(db, recipient=USER_A)
    with pytest.raises(PermissionDeniedError):
        svc.get(db, principal(USER_B), n.id)
    # Admin may access anything.
    assert svc.get(db, principal(USER_B, Role.ADMIN), n.id).id == n.id


def test_get_missing_raises_not_found(db):
    with pytest.raises(NotFoundError):
        svc.get(db, principal(USER_A), 999999)


# --------------------------------------------------------------------------- #
# mutations
# --------------------------------------------------------------------------- #
def test_mark_read_is_idempotent(db):
    n = _deliver(db, recipient=USER_A)
    first = svc.mark_read(db, principal(USER_A), n.id)
    assert first.is_read is True
    assert first.read_at is not None
    read_at = first.read_at
    # Marking again does not error nor change the timestamp.
    second = svc.mark_read(db, principal(USER_A), n.id)
    assert second.read_at == read_at


def test_mark_all_read(db):
    _deliver(db, recipient=USER_A)
    _deliver(db, recipient=USER_A)
    _deliver(db, recipient=USER_B)

    marked = svc.mark_all_read(db, principal(USER_A))
    assert marked == 2
    assert svc.unread_count(db, principal(USER_A)) == 0
    assert svc.unread_count(db, principal(USER_B)) == 1


def test_cannot_mark_others_notification_read(db):
    n = _deliver(db, recipient=USER_A)
    with pytest.raises(PermissionDeniedError):
        svc.mark_read(db, principal(USER_B), n.id)


# --------------------------------------------------------------------------- #
# API
# --------------------------------------------------------------------------- #
class _Holder:
    def __init__(self) -> None:
        self.current = principal(USER_A)


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


def test_api_list_unread_and_mark(client, session_factory):
    # Seed two notifications for USER_A directly through the service.
    session = session_factory()
    a = svc.notify(session, recipient_id=USER_A, type="system", title="a", message="m")
    svc.notify(session, recipient_id=USER_A, type="system", title="b", message="m")
    session.commit()
    a_id = a.id
    session.close()

    assert client.get("/api/notifications/unread-count").json()["unread"] == 2

    listing = client.get("/api/notifications?unread_only=true")
    assert listing.status_code == 200
    assert listing.json()["meta"]["total"] == 2

    assert client.post(f"/api/notifications/{a_id}/read").status_code == 200
    assert client.get("/api/notifications/unread-count").json()["unread"] == 1

    assert client.post("/api/notifications/read-all").json()["marked_read"] == 1
    assert client.get("/api/notifications/unread-count").json()["unread"] == 0
