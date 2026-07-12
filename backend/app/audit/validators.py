"""Activity-log business-rule guards.

The audit trail is append-only: recorded facts are immutable and the only
permitted state changes are the review lifecycle (flag then acknowledge). These
framework-agnostic guards encode that lifecycle and never touch the database,
which keeps them trivial to unit-test in isolation.

    (unflagged) ── flag ──▶ (flagged) ── acknowledge ──▶ (acknowledged)
"""
from __future__ import annotations

from app.audit.exceptions import ValidationError
from app.audit.models import ActivityLog


def validate_record_fields(
    actor_id: str, action: str, entity_type: str, entity_id: str
) -> None:
    """Rule: an audit entry must fully identify actor, action and entity."""
    for name, value in (
        ("actor_id", actor_id),
        ("action", action),
        ("entity_type", entity_type),
        ("entity_id", entity_id),
    ):
        if not (value or "").strip():
            raise ValidationError(f"An activity log entry requires a {name}")


def validate_can_flag(entry: ActivityLog) -> None:
    """Rule: an entry can only be flagged once, while still unflagged."""
    if entry.flagged:
        raise ValidationError("This activity log entry is already flagged")


def validate_can_acknowledge(entry: ActivityLog) -> None:
    """Rule: only a flagged, not-yet-acknowledged entry can be acknowledged."""
    if not entry.flagged:
        raise ValidationError(
            "Only a flagged activity log entry can be acknowledged"
        )
    if entry.acknowledged:
        raise ValidationError(
            "This activity log entry has already been acknowledged"
        )
