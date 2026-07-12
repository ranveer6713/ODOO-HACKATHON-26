"""Unit and API tests for the Maintenance module.

Covers the full state machine and every business rule:
    * Cannot approve twice
    * Cannot assign before approval
    * Cannot resolve before In Progress
    * Cannot edit resolved requests
    * Disposed assets cannot enter maintenance
    * All asset interaction happens through AssetGateway
"""
from __future__ import annotations

import pytest

from app.maintenance.exceptions import (
    NotFoundError,
    PermissionDeniedError,
    ValidationError,
)
from app.maintenance.models import MaintenancePriority, MaintenanceStatus
from app.maintenance.schemas import (
    MaintenanceCreate,
    MaintenanceUpdate,
)
from app.maintenance.service import maintenance_service as svc

from tests.conftest import (
    ASSET_DISPOSED,
    ASSET_OK,
    TECH_ID,
    asset_status,
    make_principal,
)
from app.maintenance.deps import Role


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _create(db, principal, asset_id=ASSET_OK, priority=MaintenancePriority.MEDIUM):
    return svc.create(
        db,
        principal,
        MaintenanceCreate(
            asset_id=asset_id,
            priority=priority,
            issue_description="Screen flickers intermittently",
        ),
    )


def _drive_to_in_progress(db, employee, manager, technician):
    req = _create(db, employee)
    svc.approve(db, manager, req.id)
    svc.assign_technician(db, manager, req.id, technician.id)
    svc.start(db, technician, req.id)
    return svc.get(db, manager, req.id)


# --------------------------------------------------------------------------- #
# create / disposed-asset rule
# --------------------------------------------------------------------------- #
def test_create_request_starts_pending(db, employee):
    req = _create(db, employee)
    assert req.id is not None
    assert req.status == MaintenanceStatus.PENDING
    assert req.raised_by == employee.id
    assert req.asset_id == ASSET_OK


def test_disposed_asset_cannot_enter_maintenance(db, employee):
    with pytest.raises(ValidationError) as exc:
        _create(db, employee, asset_id=ASSET_DISPOSED)
    assert "disposed" in str(exc.value).lower()


def test_create_against_unknown_asset_is_not_found(db, employee):
    with pytest.raises(NotFoundError):
        _create(db, employee, asset_id="does-not-exist")


# --------------------------------------------------------------------------- #
# approve / cannot-approve-twice rule
# --------------------------------------------------------------------------- #
def test_approve_moves_to_approved_and_takes_asset_out_of_service(
    db, employee, manager
):
    req = _create(db, employee)
    assert asset_status(db, ASSET_OK) == "available"

    approved = svc.approve(db, manager, req.id)
    assert approved.status == MaintenanceStatus.APPROVED
    assert approved.approved_by == manager.id
    assert approved.approved_at is not None
    # Asset interaction happened via the gateway.
    assert asset_status(db, ASSET_OK) == "under_maintenance"


def test_cannot_approve_twice(db, employee, manager):
    req = _create(db, employee)
    svc.approve(db, manager, req.id)
    with pytest.raises(ValidationError) as exc:
        svc.approve(db, manager, req.id)
    assert "already been approved" in str(exc.value)


# --------------------------------------------------------------------------- #
# assign / cannot-assign-before-approval rule
# --------------------------------------------------------------------------- #
def test_cannot_assign_before_approval(db, employee, manager, technician):
    req = _create(db, employee)
    with pytest.raises(ValidationError) as exc:
        svc.assign_technician(db, manager, req.id, technician.id)
    assert "before approval" in str(exc.value)


def test_assign_after_approval(db, employee, manager, technician):
    req = _create(db, employee)
    svc.approve(db, manager, req.id)
    assigned = svc.assign_technician(db, manager, req.id, technician.id)
    assert assigned.status == MaintenanceStatus.TECHNICIAN_ASSIGNED
    assert assigned.technician_id == technician.id
    assert assigned.assigned_at is not None


def test_reassignment_before_start_is_allowed(db, employee, manager, technician):
    req = _create(db, employee)
    svc.approve(db, manager, req.id)
    svc.assign_technician(db, manager, req.id, technician.id)
    other_tech = make_principal("u-tech-2", Role.TECHNICIAN)
    reassigned = svc.assign_technician(db, manager, req.id, other_tech.id)
    assert reassigned.technician_id == other_tech.id


# --------------------------------------------------------------------------- #
# start
# --------------------------------------------------------------------------- #
def test_cannot_start_before_assignment(db, employee, manager, technician):
    req = _create(db, employee)
    svc.approve(db, manager, req.id)
    with pytest.raises(ValidationError):
        svc.start(db, technician, req.id)


def test_only_assigned_technician_can_start(db, employee, manager, technician):
    req = _create(db, employee)
    svc.approve(db, manager, req.id)
    svc.assign_technician(db, manager, req.id, technician.id)
    stranger = make_principal("u-stranger", Role.TECHNICIAN)
    with pytest.raises(PermissionDeniedError):
        svc.start(db, stranger, req.id)
    started = svc.start(db, technician, req.id)
    assert started.status == MaintenanceStatus.IN_PROGRESS
    assert started.started_at is not None


# --------------------------------------------------------------------------- #
# resolve / cannot-resolve-before-in-progress rule
# --------------------------------------------------------------------------- #
def test_cannot_resolve_before_in_progress(db, employee, manager, technician):
    req = _create(db, employee)
    svc.approve(db, manager, req.id)
    svc.assign_technician(db, manager, req.id, technician.id)
    # Assigned but not started yet.
    with pytest.raises(ValidationError) as exc:
        svc.resolve(db, technician, req.id, "done")
    assert "in progress" in str(exc.value).lower()


def test_resolve_returns_asset_to_service(db, employee, manager, technician):
    req = _drive_to_in_progress(db, employee, manager, technician)
    assert asset_status(db, ASSET_OK) == "under_maintenance"

    resolved = svc.resolve(db, technician, req.id, "Replaced the panel")
    assert resolved.status == MaintenanceStatus.RESOLVED
    assert resolved.resolved_at is not None
    assert resolved.resolution_notes == "Replaced the panel"
    # Asset interaction happened via the gateway.
    assert asset_status(db, ASSET_OK) == "available"


def test_cannot_resolve_twice(db, employee, manager, technician):
    req = _drive_to_in_progress(db, employee, manager, technician)
    svc.resolve(db, technician, req.id, "fixed")
    with pytest.raises(ValidationError) as exc:
        svc.resolve(db, technician, req.id, "again")
    assert "already resolved" in str(exc.value)


# --------------------------------------------------------------------------- #
# edit / cannot-edit-resolved rule
# --------------------------------------------------------------------------- #
def test_can_edit_pending_request(db, employee):
    req = _create(db, employee)
    updated = svc.update(
        db, employee, req.id, MaintenanceUpdate(priority=MaintenancePriority.HIGH)
    )
    assert updated.priority == MaintenancePriority.HIGH


def test_cannot_edit_resolved_request(db, employee, manager, technician):
    req = _drive_to_in_progress(db, employee, manager, technician)
    svc.resolve(db, technician, req.id, "fixed")
    with pytest.raises(ValidationError) as exc:
        svc.update(
            db, manager, req.id, MaintenanceUpdate(priority=MaintenancePriority.LOW)
        )
    assert "resolved request can no longer be edited" in str(exc.value)


def test_non_author_non_manager_cannot_edit(db, employee):
    req = _create(db, employee)
    stranger = make_principal("u-stranger", Role.EMPLOYEE)
    with pytest.raises(PermissionDeniedError):
        svc.update(
            db, stranger, req.id, MaintenanceUpdate(issue_description="hijacked")
        )


# --------------------------------------------------------------------------- #
# reject branch
# --------------------------------------------------------------------------- #
def test_reject_pending_request(db, employee, manager):
    req = _create(db, employee)
    rejected = svc.reject(db, manager, req.id, "Not a real fault")
    assert rejected.status == MaintenanceStatus.REJECTED
    assert rejected.rejection_reason == "Not a real fault"
    # Rejecting must not touch the asset.
    assert asset_status(db, ASSET_OK) == "available"


def test_cannot_reject_after_approval(db, employee, manager):
    req = _create(db, employee)
    svc.approve(db, manager, req.id)
    with pytest.raises(ValidationError):
        svc.reject(db, manager, req.id, "too late")


def test_cannot_edit_rejected_request(db, employee, manager):
    req = _create(db, employee)
    svc.reject(db, manager, req.id, "no")
    with pytest.raises(ValidationError):
        svc.update(
            db, manager, req.id, MaintenanceUpdate(priority=MaintenancePriority.LOW)
        )


# --------------------------------------------------------------------------- #
# full happy-path state machine
# --------------------------------------------------------------------------- #
def test_full_workflow_happy_path(db, employee, manager, technician):
    req = _create(db, employee)
    assert req.status == MaintenanceStatus.PENDING

    assert svc.approve(db, manager, req.id).status == MaintenanceStatus.APPROVED
    assert (
        svc.assign_technician(db, manager, req.id, technician.id).status
        == MaintenanceStatus.TECHNICIAN_ASSIGNED
    )
    assert svc.start(db, technician, req.id).status == MaintenanceStatus.IN_PROGRESS
    assert (
        svc.resolve(db, technician, req.id, "all good").status
        == MaintenanceStatus.RESOLVED
    )


# --------------------------------------------------------------------------- #
# reads / visibility
# --------------------------------------------------------------------------- #
def test_employee_cannot_view_others_request(db, employee, manager):
    req = _create(db, employee)
    stranger = make_principal("u-stranger", Role.EMPLOYEE)
    with pytest.raises(PermissionDeniedError):
        svc.get(db, stranger, req.id)
    # Manager can view anything.
    assert svc.get(db, manager, req.id).id == req.id


def test_list_filters_by_status(db, employee, manager):
    r1 = _create(db, employee)
    _create(db, employee)
    svc.approve(db, manager, r1.id)

    approved, total = svc.list(
        db, manager, status=MaintenanceStatus.APPROVED
    )
    assert total == 1
    assert approved[0].id == r1.id

    pending, total_pending = svc.list(
        db, manager, status=MaintenanceStatus.PENDING
    )
    assert total_pending == 1


def test_get_missing_request_raises_not_found(db, manager):
    with pytest.raises(NotFoundError):
        svc.get(db, manager, 999999)


# --------------------------------------------------------------------------- #
# API-level tests (thin router + dependency wiring)
# --------------------------------------------------------------------------- #
def _post_create(client, asset_id=ASSET_OK):
    return client.post(
        "/api/maintenance",
        json={
            "asset_id": asset_id,
            "priority": "high",
            "issue_description": "Won't power on",
        },
    )


def test_api_create_returns_201(client, employee):
    client.as_user.current = employee
    resp = _post_create(client)
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "pending"
    assert body["priority"] == "high"
    assert body["asset_id"] == ASSET_OK


def test_api_disposed_asset_rejected(client, employee):
    client.as_user.current = employee
    resp = _post_create(client, asset_id=ASSET_DISPOSED)
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "validation_error"


def test_api_full_lifecycle(client, employee, manager, technician):
    client.as_user.current = employee
    req_id = _post_create(client).json()["id"]

    client.as_user.current = manager
    assert client.post(f"/api/maintenance/{req_id}/approve").status_code == 200
    assign = client.post(
        f"/api/maintenance/{req_id}/assign",
        json={"technician_id": TECH_ID},
    )
    assert assign.status_code == 200
    assert assign.json()["status"] == "technician_assigned"

    client.as_user.current = technician
    assert client.post(f"/api/maintenance/{req_id}/start").status_code == 200
    resolve = client.post(
        f"/api/maintenance/{req_id}/resolve",
        json={"resolution_notes": "Swapped the PSU"},
    )
    assert resolve.status_code == 200
    assert resolve.json()["status"] == "resolved"


def test_api_approve_requires_manager_role(client, employee):
    client.as_user.current = employee
    req_id = _post_create(client).json()["id"]
    # Employee lacks the manager role -> 403.
    resp = client.post(f"/api/maintenance/{req_id}/approve")
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "permission_denied"


def test_api_cannot_approve_twice(client, employee, manager):
    client.as_user.current = employee
    req_id = _post_create(client).json()["id"]
    client.as_user.current = manager
    assert client.post(f"/api/maintenance/{req_id}/approve").status_code == 200
    resp = client.post(f"/api/maintenance/{req_id}/approve")
    assert resp.status_code == 400
    assert "already been approved" in resp.json()["error"]["message"]


def test_api_list_and_get_and_delete(client, employee):
    client.as_user.current = employee
    req_id = _post_create(client).json()["id"]

    listing = client.get("/api/maintenance")
    assert listing.status_code == 200
    body = listing.json()
    assert body["meta"]["total"] == 1
    assert body["items"][0]["id"] == req_id

    got = client.get(f"/api/maintenance/{req_id}")
    assert got.status_code == 200

    deleted = client.delete(f"/api/maintenance/{req_id}")
    assert deleted.status_code == 204
    assert client.get(f"/api/maintenance/{req_id}").status_code == 404
