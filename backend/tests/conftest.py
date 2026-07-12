"""Shared pytest fixtures for the Maintenance module.

The module is exercised in complete isolation: an in-memory SQLite database holds
the module-owned ``maintenance_requests`` table plus a stand-in ``assets`` table
that satisfies the AssetGateway contract (``id``, ``name``, ``status``). The
foundation-owned ``get_db`` and ``get_current_user`` dependencies are overridden
so no real database engine or JWT stack is required.
"""
from __future__ import annotations

from typing import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.maintenance import deps, register_routes
from app.maintenance.deps import Base, Principal, Role
from app.maintenance.models import MaintenanceRequest  # noqa: F401  (registers table)

# Maintenance workflow actions write to the audit trail and deliver
# notifications, so those sibling tables must exist in the isolated test DB.
from app.audit.deps import Base as AuditBase
from app.audit.models import ActivityLog  # noqa: F401  (registers table)
from app.notifications.deps import Base as NotificationBase
from app.notifications.models import Notification  # noqa: F401  (registers table)

# Convenient string identifiers used across the test-suite.
EMPLOYEE_ID = "u-employee"
OTHER_EMPLOYEE_ID = "u-other"
MANAGER_ID = "u-manager"
TECH_ID = "u-tech"
ADMIN_ID = "u-admin"

ASSET_OK = "a-100"
ASSET_DISPOSED = "a-disposed"


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
        conn.execute(
            text("INSERT INTO assets (id, name, status) VALUES (:id, :n, :s)"),
            {"id": ASSET_OK, "n": "Projector", "s": "available"},
        )
        conn.execute(
            text("INSERT INTO assets (id, name, status) VALUES (:id, :n, :s)"),
            {"id": ASSET_DISPOSED, "n": "Old Laptop", "s": "disposed"},
        )
    try:
        yield eng
    finally:
        NotificationBase.metadata.drop_all(bind=eng)
        AuditBase.metadata.drop_all(bind=eng)
        Base.metadata.drop_all(bind=eng)
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


def make_principal(user_id: str, role: Role) -> Principal:
    return Principal(id=user_id, role=role)


# Ready-made principals.
@pytest.fixture()
def employee() -> Principal:
    return make_principal(EMPLOYEE_ID, Role.EMPLOYEE)


@pytest.fixture()
def manager() -> Principal:
    return make_principal(MANAGER_ID, Role.ASSET_MANAGER)


@pytest.fixture()
def technician() -> Principal:
    return make_principal(TECH_ID, Role.TECHNICIAN)


@pytest.fixture()
def admin() -> Principal:
    return make_principal(ADMIN_ID, Role.ADMIN)


def asset_status(db: Session, asset_id: str) -> str:
    return db.execute(
        text("SELECT status FROM assets WHERE id = :id"), {"id": asset_id}
    ).scalar_one()


class _PrincipalHolder:
    """Mutable holder so a test can switch the acting principal per request."""

    def __init__(self) -> None:
        self.current = make_principal(EMPLOYEE_ID, Role.EMPLOYEE)


@pytest.fixture()
def client(SessionLocal) -> Iterator[TestClient]:
    app = FastAPI()
    register_routes(app)

    holder = _PrincipalHolder()

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
    # Expose the holder so tests can flip the acting user: client.as_user(principal)
    test_client.as_user = holder  # type: ignore[attr-defined]
    yield test_client
