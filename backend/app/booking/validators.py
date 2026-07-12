"""Booking workflow state-transition and scheduling guards.

The single source of truth for the legal booking state machine plus its two
scheduling rules (a valid time window and no double-booking). Every illegal
transition or conflicting reservation raises a clear error instead of silently
corrupting the schedule. The service layer calls these guards before mutating a
booking; they never touch the database, which keeps them trivial to unit-test in
isolation.

    PENDING ── approve ──▶ APPROVED ── check_out ──▶ CHECKED_OUT ── check_in ──▶ CHECKED_IN
       │                      │
       ├── reject ──▶ REJECTED│
       └────── cancel ────────┴──▶ CANCELLED   (only before check-out)
"""
from __future__ import annotations

from datetime import datetime
from typing import Sequence

from app.booking.exceptions import ConflictError, ValidationError
from app.booking.models import Booking, BookingStatus


def validate_time_window(start_time: datetime, end_time: datetime, now: datetime) -> None:
    """Rule: a booking must span a positive window that does not end in the past."""
    if end_time <= start_time:
        raise ValidationError("A booking must end after it starts")
    if end_time <= now:
        raise ValidationError("A booking cannot be made entirely in the past")


def validate_no_conflict(conflicts: Sequence[Booking]) -> None:
    """Rule: an asset cannot be double-booked for overlapping time windows."""
    if conflicts:
        clash = conflicts[0]
        raise ConflictError(
            f"This asset is already booked for an overlapping period "
            f"(booking {clash.id}: {clash.status.value})"
        )


def validate_can_approve(booking: Booking) -> None:
    """Rule: a booking may be approved once, and only from PENDING."""
    if booking.status == BookingStatus.APPROVED:
        raise ValidationError("This booking has already been approved")
    if booking.status != BookingStatus.PENDING:
        raise ValidationError(
            f"Only pending bookings can be approved "
            f"(current status: '{booking.status.value}')"
        )


def validate_can_reject(booking: Booking) -> None:
    """Rule: only a still-pending booking may be rejected."""
    if booking.status == BookingStatus.REJECTED:
        raise ValidationError("This booking has already been rejected")
    if booking.status != BookingStatus.PENDING:
        raise ValidationError(
            f"Only pending bookings can be rejected "
            f"(current status: '{booking.status.value}')"
        )


def validate_can_check_out(booking: Booking) -> None:
    """Rule: an asset can only be checked out once the booking is approved."""
    if booking.status == BookingStatus.CHECKED_OUT:
        raise ValidationError("This booking has already been checked out")
    if booking.status != BookingStatus.APPROVED:
        raise ValidationError(
            "An asset can only be checked out for an approved booking "
            f"(current status: '{booking.status.value}')"
        )


def validate_can_check_in(booking: Booking) -> None:
    """Rule: an asset can only be checked in once it has been checked out."""
    if booking.status == BookingStatus.CHECKED_IN:
        raise ValidationError("This booking has already been checked in")
    if booking.status != BookingStatus.CHECKED_OUT:
        raise ValidationError(
            "An asset can only be checked in after it has been checked out "
            f"(current status: '{booking.status.value}')"
        )


def validate_can_cancel(booking: Booking) -> None:
    """Rule: a booking can be cancelled only before the asset is picked up."""
    if booking.status in (
        BookingStatus.CHECKED_OUT,
        BookingStatus.CHECKED_IN,
    ):
        raise ValidationError(
            "A booking cannot be cancelled once the asset has been checked out"
        )
    if booking.status in (BookingStatus.REJECTED, BookingStatus.CANCELLED):
        raise ValidationError(
            f"A '{booking.status.value}' booking cannot be cancelled"
        )


def validate_editable(booking: Booking) -> None:
    """Rule: only a still-pending booking may have its details edited."""
    if booking.status != BookingStatus.PENDING:
        raise ValidationError(
            "Only a pending booking can be edited "
            f"(current status: '{booking.status.value}')"
        )
