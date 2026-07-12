"""Notification persistence model and category enumeration.

Owns exactly one table: ``notifications``. The recipient is stored as a plain
string foreign key (the string-FK integration contract); no ``ForeignKey``
constraint is declared against the foundation-owned ``users`` table, so the model
registers cleanly in isolation.
"""
from __future__ import annotations

import enum
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Enum, Integer, String, Text

from app.notifications.deps import Base


class NotificationType(str, enum.Enum):
    """The originating domain of a notification."""

    MAINTENANCE = "maintenance"
    BOOKING = "booking"
    AUDIT = "audit"
    SYSTEM = "system"


class NotificationSeverity(str, enum.Enum):
    """How much attention a notification warrants.

    Mirrors the activity trail's severity vocabulary so the two surfaces speak
    the same language. Notifications default to :attr:`INFO`; sibling services
    may raise the severity (e.g. a flagged action or a breached SLA) so the
    recipient inbox can surface a dedicated *Critical* view.
    """

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _enum_values(enum_cls):
    """Persist enums by their ``.value`` (readable lowercase) in both directions."""
    return [member.value for member in enum_cls]


class Notification(Base):
    """A single message delivered to one recipient's inbox."""

    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)

    # String foreign key into the foundation-owned ``users`` table.
    recipient_id = Column(String(64), nullable=False, index=True)

    type = Column(
        Enum(
            NotificationType,
            native_enum=False,
            values_callable=_enum_values,
            length=20,
        ),
        nullable=False,
        default=NotificationType.SYSTEM,
        index=True,
    )

    severity = Column(
        Enum(
            NotificationSeverity,
            native_enum=False,
            values_callable=_enum_values,
            length=20,
        ),
        nullable=False,
        default=NotificationSeverity.INFO,
        index=True,
    )

    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)

    # Optional back-reference to the entity that triggered the notification.
    entity_type = Column(String(64), nullable=True, index=True)
    entity_id = Column(String(64), nullable=True, index=True)

    is_read = Column(Boolean, nullable=False, default=False, index=True)
    read_at = Column(DateTime(timezone=True), nullable=True)

    # Archive lifecycle — an archived message is hidden from the default inbox
    # views but retained (never deleted) so the audit story stays intact.
    archived = Column(Boolean, nullable=False, default=False, index=True)
    archived_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return (
            f"<Notification id={self.id} recipient_id={self.recipient_id!r} "
            f"type={self.type.value if self.type else None!r} read={self.is_read}>"
        )
