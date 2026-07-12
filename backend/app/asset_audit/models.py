"""Asset Audit persistence models and workflow enumerations.

Owns exactly two tables:

    * ``audit_cycles`` — an audit campaign scoped to a department / location and
      run over a date range, driven through the Created -> Active -> Closed
      lifecycle.
    * ``audit_items``  — one asset enrolled in a cycle and assigned to an
      auditor, carrying the auditor's verification verdict.

References to users and assets are stored as plain string foreign keys (the
string-FK integration contract); no ``ForeignKey`` constraint is declared against
tables this module does not own. The ``audit_items.audit_cycle_id`` relationship
*is* a real foreign key because both tables are owned here.
"""
from __future__ import annotations

import enum
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.asset_audit.deps import Base


class AuditCycleStatus(str, enum.Enum):
    """The audit-cycle lifecycle.

    Happy path::

        CREATED -> ACTIVE -> CLOSED

    A closed cycle is locked: neither the cycle nor its items may be edited.
    """

    CREATED = "created"
    ACTIVE = "active"
    CLOSED = "closed"


class AuditItemStatus(str, enum.Enum):
    """The auditor's verification verdict for an enrolled asset.

    ``None`` (the column default) means the asset has not been verified yet;
    once set, the item is locked (an asset is never verified twice in a cycle).
    """

    VERIFIED = "verified"
    MISSING = "missing"
    DAMAGED = "damaged"


# Verdicts that count as a discrepancy (surface in the discrepancy report).
DISCREPANCY_STATUSES = frozenset({AuditItemStatus.MISSING, AuditItemStatus.DAMAGED})


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _enum_values(enum_cls):
    """Persist enums by their ``.value`` (readable lowercase) in both directions."""
    return [member.value for member in enum_cls]


class AuditCycle(Base):
    """An audit campaign over a department/location for a fixed date range."""

    __tablename__ = "audit_cycles"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(255), nullable=False)

    # Scope of the audit. Department is a string FK into a foundation-owned table;
    # location is free-form text. Both are optional (an audit may be estate-wide).
    department_id = Column(String(64), nullable=True, index=True)
    location = Column(String(255), nullable=True)

    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)

    # Who created the cycle (string FK into the foundation ``users`` table).
    created_by = Column(String(64), nullable=False, index=True)

    status = Column(
        Enum(
            AuditCycleStatus,
            native_enum=False,
            values_callable=_enum_values,
            length=20,
        ),
        nullable=False,
        default=AuditCycleStatus.CREATED,
        index=True,
    )

    started_at = Column(DateTime(timezone=True), nullable=True)
    closed_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
        onupdate=_utcnow,
    )

    items = relationship(
        "AuditItem",
        back_populates="cycle",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return (
            f"<AuditCycle id={self.id} name={self.name!r} "
            f"status={self.status.value if self.status else None!r}>"
        )


class AuditItem(Base):
    """One asset enrolled in a cycle, assigned to an auditor, awaiting a verdict."""

    __tablename__ = "audit_items"
    __table_args__ = (
        # One asset appears only once per audit cycle.
        UniqueConstraint("audit_cycle_id", "asset_id", name="uq_audit_item_asset"),
    )

    id = Column(Integer, primary_key=True, index=True)

    # Real FK: the parent cycle is owned by this module.
    audit_cycle_id = Column(
        Integer,
        ForeignKey("audit_cycles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # String foreign keys into foundation-owned tables (no DB-level constraint).
    asset_id = Column(String(64), nullable=False, index=True)
    auditor_id = Column(String(64), nullable=False, index=True)

    status = Column(
        Enum(
            AuditItemStatus,
            native_enum=False,
            values_callable=_enum_values,
            length=20,
        ),
        nullable=True,
        index=True,
    )

    remarks = Column(Text, nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
        onupdate=_utcnow,
    )

    cycle = relationship("AuditCycle", back_populates="items")

    @property
    def is_verified(self) -> bool:
        """True once the auditor has recorded any verdict for this item."""
        return self.verified_at is not None

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return (
            f"<AuditItem id={self.id} cycle={self.audit_cycle_id} "
            f"asset_id={self.asset_id!r} "
            f"status={self.status.value if self.status else None!r}>"
        )
