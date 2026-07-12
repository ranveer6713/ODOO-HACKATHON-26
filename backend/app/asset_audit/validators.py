"""Asset Audit workflow state-transition and business-rule guards.

This is the single source of truth for the legal state machine and the module's
business rules. Every illegal transition raises a clear :class:`ValidationError`
instead of silently corrupting a cycle. The service layer calls these guards
before mutating state; they never touch the database, which keeps them trivial to
unit-test in isolation.

    CREATED ── start ──▶ ACTIVE ── close ──▶ CLOSED (locked)

Rules enforced here:
    * A closed audit cannot be edited (cycle or items).
    * An asset cannot be verified twice in the same cycle.
    * An empty audit cannot be closed.
    * ``end_date`` cannot precede ``start_date``.
"""
from __future__ import annotations

from datetime import date
from typing import Optional

from app.asset_audit.exceptions import ValidationError
from app.asset_audit.models import AuditCycle, AuditCycleStatus, AuditItem


def validate_dates(start_date: date, end_date: date) -> None:
    """Rule: an audit window must not end before it begins."""
    if end_date < start_date:
        raise ValidationError("end_date cannot be earlier than start_date")


def validate_cycle_editable(cycle: AuditCycle) -> None:
    """Rule: a closed audit is locked and can no longer be edited."""
    if cycle.status == AuditCycleStatus.CLOSED:
        raise ValidationError("A closed audit cannot be edited")


def validate_can_start(cycle: AuditCycle) -> None:
    """Rule: only a freshly-created cycle can be started (once)."""
    if cycle.status == AuditCycleStatus.ACTIVE:
        raise ValidationError("This audit cycle has already been started")
    if cycle.status == AuditCycleStatus.CLOSED:
        raise ValidationError("A closed audit cannot be started")
    if cycle.status != AuditCycleStatus.CREATED:
        raise ValidationError(
            f"Only a created audit cycle can be started "
            f"(current status: '{cycle.status.value}')"
        )


def validate_can_close(cycle: AuditCycle, item_count: int) -> None:
    """Rule: only a started, non-empty audit can be closed (once)."""
    if cycle.status == AuditCycleStatus.CLOSED:
        raise ValidationError("This audit cycle is already closed")
    if cycle.status != AuditCycleStatus.ACTIVE:
        raise ValidationError(
            "An audit cycle must be started before it can be closed "
            f"(current status: '{cycle.status.value}')"
        )
    if item_count <= 0:
        raise ValidationError("Cannot close an empty audit")


def validate_can_add_item(cycle: AuditCycle) -> None:
    """Rule: assets/auditors can only be enrolled while the audit is not closed."""
    if cycle.status == AuditCycleStatus.CLOSED:
        raise ValidationError("Cannot modify a closed audit")


def validate_no_duplicate(
    existing: Optional[AuditItem], asset_id: str, auditor_id: str
) -> None:
    """Enforce the two enrollment uniqueness rules.

    * *Cannot duplicate auditor entries* — the same auditor already holds this
      exact asset in the cycle.
    * *Cannot duplicate asset* — the asset is already enrolled (under any
      auditor); one asset appears only once per cycle.
    """
    if existing is None:
        return
    if existing.auditor_id == auditor_id:
        raise ValidationError(
            f"Auditor '{auditor_id}' is already assigned to asset "
            f"'{asset_id}' in this audit cycle"
        )
    raise ValidationError(
        f"Asset '{asset_id}' is already enrolled in this audit cycle"
    )


def validate_item_verifiable(item: AuditItem, cycle: AuditCycle) -> None:
    """Rule: an item can be verified once, and only while the cycle is active."""
    if cycle.status == AuditCycleStatus.CLOSED:
        raise ValidationError("Cannot modify a closed audit")
    if cycle.status != AuditCycleStatus.ACTIVE:
        raise ValidationError(
            "The audit cycle must be started before assets can be verified"
        )
    if item.is_verified:
        raise ValidationError(
            "This asset has already been verified in this audit cycle"
        )
