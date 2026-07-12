"""Activity-log persistence model and audit enumerations.

Owns exactly one table: ``activity_logs`` — the append-only audit trail that
every workflow action across the backend writes to. Actors and entities are
referenced as plain strings (the string-FK integration contract); no
``ForeignKey`` constraint is declared against tables this module does not own.
"""
from __future__ import annotations

import enum
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Enum, Integer, String, Text

from app.audit.deps import Base


class AuditSeverity(str, enum.Enum):
    """How much attention a logged action warrants."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _enum_values(enum_cls):
    """Persist enums by their ``.value`` (readable lowercase) in both directions."""
    return [member.value for member in enum_cls]


class ActivityLog(Base):
    """One immutable audit-trail entry describing a workflow action.

    Entries are append-only: the only permitted mutations are the review
    lifecycle (flag / acknowledge), never the recorded facts themselves.
    """

    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)

    # Who performed the action (string FK into the foundation ``users`` table).
    actor_id = Column(String(64), nullable=False, index=True)

    # What happened, and to which entity (free-form strings kept deliberately
    # decoupled from any sibling module's internal enums).
    action = Column(String(64), nullable=False, index=True)
    entity_type = Column(String(64), nullable=False, index=True)
    entity_id = Column(String(64), nullable=False, index=True)

    description = Column(Text, nullable=True)

    severity = Column(
        Enum(
            AuditSeverity,
            native_enum=False,
            values_callable=_enum_values,
            length=20,
        ),
        nullable=False,
        default=AuditSeverity.INFO,
        index=True,
    )

    # Review lifecycle (the only mutable facet of an otherwise immutable entry).
    flagged = Column(Boolean, nullable=False, default=False, index=True)
    flagged_by = Column(String(64), nullable=True)
    flag_reason = Column(Text, nullable=True)
    flagged_at = Column(DateTime(timezone=True), nullable=True)

    acknowledged = Column(Boolean, nullable=False, default=False)
    acknowledged_by = Column(String(64), nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return (
            f"<ActivityLog id={self.id} actor_id={self.actor_id!r} "
            f"action={self.action!r} entity={self.entity_type}:{self.entity_id}>"
        )
