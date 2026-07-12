"""Maintenance request persistence model and workflow enumerations.

Owns exactly one table: ``maintenance_requests``. References to users and assets
are stored as plain string foreign keys (the string-FK integration contract); no
``ForeignKey`` constraint is declared against tables this module does not own, so
the model registers cleanly in isolation and never depends on another team's
metadata being present.
"""
from __future__ import annotations

import enum
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Enum, Integer, String, Text

from app.maintenance.deps import Base


class MaintenancePriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class MaintenanceStatus(str, enum.Enum):
    """The maintenance workflow states.

    Happy path::

        PENDING -> APPROVED -> TECHNICIAN_ASSIGNED -> IN_PROGRESS -> RESOLVED

    A pending request may instead be REJECTED, which terminates the workflow.
    """

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    TECHNICIAN_ASSIGNED = "technician_assigned"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _enum_values(enum_cls):
    """Persist enums by their ``.value`` (readable lowercase) in both directions."""
    return [member.value for member in enum_cls]


class MaintenanceRequest(Base):
    """A repair/service request raised against an asset and driven through the
    approval -> assignment -> resolution workflow."""

    __tablename__ = "maintenance_requests"

    id = Column(Integer, primary_key=True, index=True)

    # String foreign keys into foundation-owned tables (no DB-level constraint).
    asset_id = Column(String(64), nullable=False, index=True)
    raised_by = Column(String(64), nullable=False, index=True)

    priority = Column(
        Enum(
            MaintenancePriority,
            native_enum=False,
            values_callable=_enum_values,
            length=20,
        ),
        nullable=False,
        default=MaintenancePriority.MEDIUM,
        index=True,
    )

    issue_description = Column(Text, nullable=False)
    photo_url = Column(String(1024), nullable=True)

    status = Column(
        Enum(
            MaintenanceStatus,
            native_enum=False,
            values_callable=_enum_values,
            length=30,
        ),
        nullable=False,
        default=MaintenanceStatus.PENDING,
        index=True,
    )

    approved_by = Column(String(64), nullable=True)
    technician_id = Column(String(64), nullable=True, index=True)

    rejection_reason = Column(Text, nullable=True)
    resolution_notes = Column(Text, nullable=True)

    approved_at = Column(DateTime(timezone=True), nullable=True)
    assigned_at = Column(DateTime(timezone=True), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
        onupdate=_utcnow,
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return (
            f"<MaintenanceRequest id={self.id} asset_id={self.asset_id!r} "
            f"status={self.status.value if self.status else None!r}>"
        )
