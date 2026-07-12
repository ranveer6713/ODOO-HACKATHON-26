"""Booking persistence model and workflow enumerations.

Owns exactly one table: ``bookings``. References to users and assets are stored
as plain string foreign keys (the string-FK integration contract); no
``ForeignKey`` constraint is declared against tables this module does not own, so
the model registers cleanly in isolation.
"""
from __future__ import annotations

import enum
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Enum, Integer, String, Text

from app.booking.deps import Base


class BookingStatus(str, enum.Enum):
    """The booking workflow states.

    Happy path::

        PENDING -> APPROVED -> CHECKED_OUT -> CHECKED_IN

    A pending request may instead be REJECTED. A booking may be CANCELLED while
    it is still PENDING or APPROVED (before the asset has been picked up).
    """

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CHECKED_OUT = "checked_out"
    CHECKED_IN = "checked_in"
    CANCELLED = "cancelled"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _enum_values(enum_cls):
    """Persist enums by their ``.value`` (readable lowercase) in both directions."""
    return [member.value for member in enum_cls]


class Booking(Base):
    """A time-bounded reservation of an asset, driven through the
    approval -> checkout -> checkin workflow."""

    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)

    # String foreign keys into foundation-owned tables (no DB-level constraint).
    asset_id = Column(String(64), nullable=False, index=True)
    requested_by = Column(String(64), nullable=False, index=True)

    purpose = Column(Text, nullable=False)

    start_time = Column(DateTime(timezone=True), nullable=False, index=True)
    end_time = Column(DateTime(timezone=True), nullable=False, index=True)

    status = Column(
        Enum(
            BookingStatus,
            native_enum=False,
            values_callable=_enum_values,
            length=20,
        ),
        nullable=False,
        default=BookingStatus.PENDING,
        index=True,
    )

    approved_by = Column(String(64), nullable=True)
    rejection_reason = Column(Text, nullable=True)

    cancelled_by = Column(String(64), nullable=True)
    cancellation_reason = Column(Text, nullable=True)

    approved_at = Column(DateTime(timezone=True), nullable=True)
    checked_out_at = Column(DateTime(timezone=True), nullable=True)
    checked_in_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
        onupdate=_utcnow,
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return (
            f"<Booking id={self.id} asset_id={self.asset_id!r} "
            f"status={self.status.value if self.status else None!r}>"
        )
