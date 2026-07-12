"""Maintenance workflow state-transition guards.

This is the single source of truth for the legal state machine. Every illegal
transition raises a clear :class:`ValidationError` instead of silently corrupting
a request. The service layer calls these guards before mutating a request; they
never touch the database, which keeps them trivial to unit-test in isolation.

    PENDING ── approve ──▶ APPROVED ── assign ──▶ TECHNICIAN_ASSIGNED
       │                                                  │
       └── reject ──▶ REJECTED                      start │
                                                          ▼
                        RESOLVED ◀── resolve ──── IN_PROGRESS
"""
from __future__ import annotations

from app.maintenance.exceptions import ValidationError
from app.maintenance.models import MaintenanceRequest, MaintenanceStatus


def validate_can_approve(request: MaintenanceRequest) -> None:
    """Rule: a request may be approved once, and only from PENDING."""
    if request.status == MaintenanceStatus.APPROVED:
        raise ValidationError("This request has already been approved")
    if request.status != MaintenanceStatus.PENDING:
        raise ValidationError(
            f"Only pending requests can be approved "
            f"(current status: '{request.status.value}')"
        )


def validate_can_reject(request: MaintenanceRequest) -> None:
    """Rule: only a still-pending request may be rejected."""
    if request.status == MaintenanceStatus.REJECTED:
        raise ValidationError("This request has already been rejected")
    if request.status != MaintenanceStatus.PENDING:
        raise ValidationError(
            f"Only pending requests can be rejected "
            f"(current status: '{request.status.value}')"
        )


def validate_can_assign(request: MaintenanceRequest) -> None:
    """Rule: a technician cannot be assigned before approval.

    Reassignment while already assigned is permitted (e.g. handing the job to a
    different technician before work starts).
    """
    if request.status in (
        MaintenanceStatus.PENDING,
        MaintenanceStatus.REJECTED,
    ):
        raise ValidationError("A technician cannot be assigned before approval")
    if request.status not in (
        MaintenanceStatus.APPROVED,
        MaintenanceStatus.TECHNICIAN_ASSIGNED,
    ):
        raise ValidationError(
            f"A technician cannot be assigned in status '{request.status.value}'"
        )


def validate_can_start(request: MaintenanceRequest) -> None:
    """Rule: work can only start once a technician has been assigned."""
    if request.status != MaintenanceStatus.TECHNICIAN_ASSIGNED:
        raise ValidationError(
            "Work can only start once a technician has been assigned "
            f"(current status: '{request.status.value}')"
        )


def validate_can_resolve(request: MaintenanceRequest) -> None:
    """Rule: a request cannot be resolved before it is In Progress."""
    if request.status == MaintenanceStatus.RESOLVED:
        raise ValidationError("This request is already resolved")
    if request.status != MaintenanceStatus.IN_PROGRESS:
        raise ValidationError(
            "A request cannot be resolved before work is in progress "
            f"(current status: '{request.status.value}')"
        )


def validate_editable(request: MaintenanceRequest) -> None:
    """Rule: resolved (and rejected, i.e. terminal) requests cannot be edited."""
    if request.status == MaintenanceStatus.RESOLVED:
        raise ValidationError("A resolved request can no longer be edited")
    if request.status == MaintenanceStatus.REJECTED:
        raise ValidationError("A rejected request can no longer be edited")
