"""Booking management business logic and workflow orchestration.

The service is the only layer that mutates state. It coordinates:
    * the workflow state machine and scheduling rules (delegated to
      :mod:`validators`),
    * asset interactions (delegated exclusively to :class:`AssetGateway`),
    * the audit trail — every workflow action is recorded via
      :class:`AuditService` (the "every workflow action creates an activity log
      entry" rule),
    * recipient notifications via the shared :class:`NotificationService`,
    * record-level access control, and
    * transaction boundaries (commit / rollback).

Collaborators are injected (defaulting to the shared singletons) so there is no
global mutable state and the module stays unit-testable. The audit-log and
notification writes participate in this service's transaction — they flush but
do not commit — so a booking change and its trail/notification are persisted
atomically. Routers stay thin by holding no logic of their own.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional, Tuple

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.audit.models import AuditSeverity
from app.audit.service import AuditService, audit_service
from app.booking import validators
from app.booking.deps import Principal, Role
from app.booking.exceptions import NotFoundError, PermissionDeniedError
from app.booking.gateway import AssetGateway, asset_gateway
from app.booking.models import Booking, BookingStatus
from app.booking.schemas import BookingCreate, BookingUpdate
from app.notifications.models import NotificationType
from app.notifications.service import NotificationService, notification_service

_MANAGER_ROLES = (Role.ASSET_MANAGER, Role.ADMIN)

# Booking states that still occupy the asset's calendar for overlap purposes.
_ACTIVE_STATES = (
    BookingStatus.PENDING,
    BookingStatus.APPROVED,
    BookingStatus.CHECKED_OUT,
)

_ENTITY = "booking"

_SORTABLE_FIELDS = {
    "created_at": Booking.created_at,
    "updated_at": Booking.updated_at,
    "start_time": Booking.start_time,
    "end_time": Booking.end_time,
    "status": Booking.status,
    "id": Booking.id,
}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class BookingService:
    """Stateless orchestrator; the DB session is passed in per call."""

    def __init__(
        self,
        *,
        assets: Optional[AssetGateway] = None,
        activity_log: Optional[AuditService] = None,
        notifier: Optional[NotificationService] = None,
    ) -> None:
        # Dependency injection with sensible defaults; no global mutable state.
        self._assets = assets or asset_gateway
        self._activity_log = activity_log or audit_service
        self._notifier = notifier or notification_service

    # ------------------------------------------------------------------ access
    def _is_manager(self, principal: Principal) -> bool:
        return principal.role in _MANAGER_ROLES

    def _visibility_filter(self, principal: Principal):
        """Non-managers only see bookings they raised."""
        if self._is_manager(principal):
            return None
        return Booking.requested_by == principal.id

    def _require(self, db: Session, booking_id: int) -> Booking:
        booking = db.get(Booking, booking_id)
        if booking is None:
            raise NotFoundError(f"Booking {booking_id} does not exist")
        return booking

    def _ensure_owner_or_manager(
        self, principal: Principal, booking: Booking, action: str
    ) -> None:
        if self._is_manager(principal):
            return
        if booking.requested_by != principal.id:
            raise PermissionDeniedError(
                f"Only the requester or an asset manager can {action} this booking"
            )

    # ---------------------------------------------------------------- helpers
    def _conflicts(
        self,
        db: Session,
        asset_id: str,
        start_time: datetime,
        end_time: datetime,
        exclude_id: Optional[int] = None,
    ) -> List[Booking]:
        """Active bookings for the asset whose window overlaps ``[start, end)``."""
        query = select(Booking).where(
            Booking.asset_id == asset_id,
            Booking.status.in_(_ACTIVE_STATES),
            Booking.start_time < end_time,
            Booking.end_time > start_time,
        )
        if exclude_id is not None:
            query = query.where(Booking.id != exclude_id)
        return list(db.execute(query).scalars().all())

    def _log(
        self,
        db: Session,
        principal: Principal,
        booking: Booking,
        action: str,
        description: str,
        severity: AuditSeverity = AuditSeverity.INFO,
    ) -> None:
        self._activity_log.record(
            db,
            actor_id=principal.id,
            action=action,
            entity_type=_ENTITY,
            entity_id=str(booking.id),
            description=description,
            severity=severity,
        )

    def _notify_requester(
        self, db: Session, booking: Booking, title: str, message: str
    ) -> None:
        self._notifier.notify(
            db,
            recipient_id=booking.requested_by,
            type=NotificationType.BOOKING,
            title=title,
            message=message,
            entity_type=_ENTITY,
            entity_id=str(booking.id),
        )

    # ------------------------------------------------------------------- reads
    def get(self, db: Session, principal: Principal, booking_id: int) -> Booking:
        booking = self._require(db, booking_id)
        if not self._is_manager(principal) and booking.requested_by != principal.id:
            raise PermissionDeniedError(
                "You are not allowed to view this booking"
            )
        return booking

    def list(
        self,
        db: Session,
        principal: Principal,
        *,
        status: Optional[BookingStatus] = None,
        asset_id: Optional[str] = None,
        requested_by: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: str = "start_time",
        order: str = "desc",
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Booking], int]:
        conditions = []
        vis = self._visibility_filter(principal)
        if vis is not None:
            conditions.append(vis)
        if status is not None:
            conditions.append(Booking.status == status)
        if asset_id is not None:
            conditions.append(Booking.asset_id == asset_id)
        if requested_by is not None:
            conditions.append(Booking.requested_by == requested_by)
        if search:
            conditions.append(Booking.purpose.ilike(f"%{search.strip()}%"))

        where = and_(*conditions) if conditions else None

        count_query = select(func.count()).select_from(Booking)
        if where is not None:
            count_query = count_query.where(where)
        total = db.execute(count_query).scalar_one()

        column = _SORTABLE_FIELDS.get(sort_by, Booking.start_time)
        column = column.desc() if order.lower() == "desc" else column.asc()

        query = select(Booking)
        if where is not None:
            query = query.where(where)
        query = (
            query.order_by(column, Booking.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        rows = list(db.execute(query).scalars().all())
        return rows, total

    # --------------------------------------------------------------- lifecycle
    def create(
        self, db: Session, principal: Principal, data: BookingCreate
    ) -> Booking:
        # Rule: unavailable assets cannot be booked (checked via the gateway).
        self._assets.assert_bookable(db, data.asset_id)
        # Rule: a valid, future-ending window.
        validators.validate_time_window(data.start_time, data.end_time, _utcnow())
        # Rule: no double-booking of the same asset for overlapping windows.
        validators.validate_no_conflict(
            self._conflicts(db, data.asset_id, data.start_time, data.end_time)
        )

        booking = Booking(
            asset_id=data.asset_id,
            requested_by=principal.id,
            purpose=data.purpose,
            start_time=data.start_time,
            end_time=data.end_time,
            status=BookingStatus.PENDING,
        )
        db.add(booking)
        db.flush()

        self._log(
            db, principal, booking, "created",
            f"Booking raised for asset {booking.asset_id}",
        )
        self._notify_requester(
            db, booking,
            "Booking submitted",
            f"Your booking for asset {booking.asset_id} is pending approval.",
        )

        db.commit()
        db.refresh(booking)
        return booking

    def update(
        self,
        db: Session,
        principal: Principal,
        booking_id: int,
        data: BookingUpdate,
    ) -> Booking:
        booking = self._require(db, booking_id)
        self._ensure_owner_or_manager(principal, booking, "edit")
        # Rule: only a pending booking can be edited.
        validators.validate_editable(booking)

        if data.purpose is not None:
            booking.purpose = data.purpose

        new_start = data.start_time or booking.start_time
        new_end = data.end_time or booking.end_time
        if data.start_time is not None or data.end_time is not None:
            validators.validate_time_window(new_start, new_end, _utcnow())
            validators.validate_no_conflict(
                self._conflicts(
                    db, booking.asset_id, new_start, new_end, exclude_id=booking.id
                )
            )
            booking.start_time = new_start
            booking.end_time = new_end

        self._log(db, principal, booking, "updated", "Booking details updated")
        db.commit()
        db.refresh(booking)
        return booking

    def delete(self, db: Session, principal: Principal, booking_id: int) -> None:
        booking = self._require(db, booking_id)
        self._ensure_owner_or_manager(principal, booking, "delete")
        # A checked-out asset must be checked in before the booking can be removed.
        if booking.status == BookingStatus.CHECKED_OUT:
            raise PermissionDeniedError(
                "Check the asset in before deleting this booking"
            )
        self._log(
            db, principal, booking, "deleted", "Booking deleted",
            severity=AuditSeverity.WARNING,
        )
        db.delete(booking)
        db.commit()

    def approve(
        self, db: Session, principal: Principal, booking_id: int
    ) -> Booking:
        booking = self._require(db, booking_id)
        # Rule: cannot approve twice / only from pending.
        validators.validate_can_approve(booking)
        # Re-check overlap at approval time in case a rival booking was approved.
        validators.validate_no_conflict(
            self._conflicts(
                db, booking.asset_id, booking.start_time, booking.end_time,
                exclude_id=booking.id,
            )
        )

        booking.status = BookingStatus.APPROVED
        booking.approved_by = principal.id
        booking.approved_at = _utcnow()
        booking.rejection_reason = None

        self._log(db, principal, booking, "approved", "Booking approved")
        self._notify_requester(
            db, booking,
            "Booking approved",
            f"Your booking for asset {booking.asset_id} was approved.",
        )

        db.commit()
        db.refresh(booking)
        return booking

    def reject(
        self, db: Session, principal: Principal, booking_id: int, reason: str
    ) -> Booking:
        booking = self._require(db, booking_id)
        validators.validate_can_reject(booking)

        booking.status = BookingStatus.REJECTED
        booking.approved_by = principal.id
        booking.rejection_reason = reason

        self._log(
            db, principal, booking, "rejected", f"Booking rejected: {reason}",
            severity=AuditSeverity.WARNING,
        )
        self._notify_requester(
            db, booking,
            "Booking rejected",
            f"Your booking for asset {booking.asset_id} was rejected: {reason}",
        )

        db.commit()
        db.refresh(booking)
        return booking

    def check_out(
        self, db: Session, principal: Principal, booking_id: int
    ) -> Booking:
        booking = self._require(db, booking_id)
        self._ensure_owner_or_manager(principal, booking, "check out")
        # Rule: only an approved booking can be checked out.
        validators.validate_can_check_out(booking)

        booking.status = BookingStatus.CHECKED_OUT
        booking.checked_out_at = _utcnow()
        # Check-out takes the asset off the shelf (asset interaction via gateway).
        self._assets.mark_booked(db, booking.asset_id)

        self._log(db, principal, booking, "checked_out", "Asset checked out")
        self._notify_requester(
            db, booking,
            "Asset checked out",
            f"You have checked out asset {booking.asset_id}.",
        )

        db.commit()
        db.refresh(booking)
        return booking

    def check_in(
        self, db: Session, principal: Principal, booking_id: int
    ) -> Booking:
        booking = self._require(db, booking_id)
        self._ensure_owner_or_manager(principal, booking, "check in")
        # Rule: only a checked-out booking can be checked in.
        validators.validate_can_check_in(booking)

        booking.status = BookingStatus.CHECKED_IN
        booking.checked_in_at = _utcnow()
        # Check-in returns the asset to service (asset interaction via gateway).
        self._assets.mark_available(db, booking.asset_id)

        self._log(db, principal, booking, "checked_in", "Asset checked in")
        self._notify_requester(
            db, booking,
            "Asset checked in",
            f"Asset {booking.asset_id} has been returned. Thank you.",
        )

        db.commit()
        db.refresh(booking)
        return booking

    def cancel(
        self,
        db: Session,
        principal: Principal,
        booking_id: int,
        reason: Optional[str] = None,
    ) -> Booking:
        booking = self._require(db, booking_id)
        self._ensure_owner_or_manager(principal, booking, "cancel")
        # Rule: a booking can only be cancelled before the asset is picked up.
        validators.validate_can_cancel(booking)

        booking.status = BookingStatus.CANCELLED
        booking.cancelled_by = principal.id
        booking.cancellation_reason = reason
        booking.cancelled_at = _utcnow()

        detail = f"Booking cancelled{f': {reason}' if reason else ''}"
        self._log(
            db, principal, booking, "cancelled", detail,
            severity=AuditSeverity.WARNING,
        )
        self._notify_requester(
            db, booking,
            "Booking cancelled",
            f"Your booking for asset {booking.asset_id} was cancelled.",
        )

        db.commit()
        db.refresh(booking)
        return booking


# Module-level singleton; stateless, so safe to share across requests.
booking_service = BookingService()
