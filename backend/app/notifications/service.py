"""Notification business logic — the reusable delivery service.

This service is the shared notification port for the whole AssetFlow backend:
Maintenance, Booking and Audit all deliver messages through
:meth:`NotificationService.notify`. It deliberately keeps two transaction
disciplines:

    * :meth:`notify` — invoked *by other services mid-transaction*. It only
      ``add`` + ``flush`` so the notification commits atomically with the
      workflow change that produced it (the caller owns the commit).
    * router-facing reads/mutations (``mark_read`` etc.) own their own commit.

Stateless; the DB session is passed in per call. No global mutable state.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional, Tuple, Union

from sqlalchemy import and_, func, select, update
from sqlalchemy.orm import Session

from app.notifications import validators
from app.notifications.deps import Principal
from app.notifications.exceptions import NotFoundError, ValidationError
from app.notifications.models import (
    Notification,
    NotificationSeverity,
    NotificationType,
)

_SORTABLE_FIELDS = {
    "created_at": Notification.created_at,
    "id": Notification.id,
    "is_read": Notification.is_read,
    "severity": Notification.severity,
}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _coerce_type(value: Union[str, NotificationType]) -> NotificationType:
    if isinstance(value, NotificationType):
        return value
    try:
        return NotificationType(value)
    except ValueError as exc:
        raise ValidationError(f"Unknown notification type '{value}'") from exc


def _coerce_severity(
    value: Union[str, NotificationSeverity]
) -> NotificationSeverity:
    if isinstance(value, NotificationSeverity):
        return value
    try:
        return NotificationSeverity(value)
    except ValueError as exc:
        raise ValidationError(f"Unknown notification severity '{value}'") from exc


class NotificationService:
    """Stateless orchestrator; the DB session is passed in per call."""

    # ------------------------------------------------------------ delivery API
    def notify(
        self,
        db: Session,
        *,
        recipient_id: str,
        type: Union[str, NotificationType],
        title: str,
        message: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        severity: Union[str, NotificationSeverity] = NotificationSeverity.INFO,
    ) -> Notification:
        """Deliver a notification to a single recipient.

        Called by sibling workflow services *inside their transaction*: this
        method never commits, so the message and the workflow mutation that
        triggered it are persisted together (or rolled back together).

        ``severity`` defaults to :attr:`NotificationSeverity.INFO`, so existing
        callers are unaffected; a caller may raise it to surface the message in
        the recipient's *Critical* inbox view.
        """
        recipient_id = validators.validate_recipient_id(recipient_id)
        validators.validate_content(title, message)

        notification = Notification(
            recipient_id=recipient_id,
            type=_coerce_type(type),
            severity=_coerce_severity(severity),
            title=title.strip(),
            message=message.strip(),
            entity_type=entity_type,
            entity_id=entity_id,
        )
        db.add(notification)
        db.flush()
        return notification

    # ------------------------------------------------------------------- reads
    def _require(self, db: Session, notification_id: int) -> Notification:
        notification = db.get(Notification, notification_id)
        if notification is None:
            raise NotFoundError(
                f"Notification {notification_id} does not exist"
            )
        return notification

    def get(
        self, db: Session, principal: Principal, notification_id: int
    ) -> Notification:
        notification = self._require(db, notification_id)
        validators.validate_can_access(notification, principal)
        return notification

    def list_for(
        self,
        db: Session,
        principal: Principal,
        *,
        unread_only: bool = False,
        read_only: bool = False,
        type: Optional[Union[str, NotificationType]] = None,
        severity: Optional[Union[str, NotificationSeverity]] = None,
        archived: Optional[bool] = None,
        sort_by: str = "created_at",
        order: str = "desc",
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Notification], int]:
        """List a recipient's notifications with optional inbox filters.

        ``archived`` defaults to ``None`` (no archive filter) to preserve the
        behaviour existing callers rely on; the UI backend passes ``False`` for
        the live inbox and ``True`` for the archive view. ``unread_only`` and
        ``read_only`` are convenience toggles for the *Unread* / *Read* tabs.
        """
        conditions = [Notification.recipient_id == principal.id]
        if unread_only:
            conditions.append(Notification.is_read.is_(False))
        if read_only:
            conditions.append(Notification.is_read.is_(True))
        if type is not None:
            conditions.append(Notification.type == _coerce_type(type))
        if severity is not None:
            conditions.append(Notification.severity == _coerce_severity(severity))
        if archived is not None:
            conditions.append(Notification.archived.is_(archived))

        where = and_(*conditions)

        total = db.execute(
            select(func.count()).select_from(Notification).where(where)
        ).scalar_one()

        column = _SORTABLE_FIELDS.get(sort_by, Notification.created_at)
        column = column.desc() if order.lower() == "desc" else column.asc()

        rows = list(
            db.execute(
                select(Notification)
                .where(where)
                .order_by(column, Notification.id.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
            .scalars()
            .all()
        )
        return rows, total

    def unread_count(self, db: Session, principal: Principal) -> int:
        return db.execute(
            select(func.count())
            .select_from(Notification)
            .where(
                Notification.recipient_id == principal.id,
                Notification.is_read.is_(False),
            )
        ).scalar_one()

    # --------------------------------------------------------------- mutations
    def mark_read(
        self, db: Session, principal: Principal, notification_id: int
    ) -> Notification:
        """Mark one notification read. Idempotent for an already-read message."""
        notification = self._require(db, notification_id)
        validators.validate_can_access(notification, principal)

        if not notification.is_read:
            notification.is_read = True
            notification.read_at = _utcnow()
            db.commit()
            db.refresh(notification)
        return notification

    def mark_all_read(self, db: Session, principal: Principal) -> int:
        """Mark every unread notification for the caller read; returns the count.

        A single bulk UPDATE keeps this O(1) round-trips regardless of inbox size
        (no per-row load or per-row mutation).
        """
        result = db.execute(
            update(Notification)
            .where(
                Notification.recipient_id == principal.id,
                Notification.is_read.is_(False),
            )
            .values(is_read=True, read_at=_utcnow())
        )
        if result.rowcount:
            db.commit()
        return result.rowcount

    def archive(
        self, db: Session, principal: Principal, notification_id: int
    ) -> Notification:
        """Archive one notification. Idempotent for an already-archived message.

        Archiving retains the row (never deletes it) and simply removes it from
        the default inbox views. Only the recipient (or an admin) may archive.
        """
        notification = self._require(db, notification_id)
        validators.validate_can_access(notification, principal)

        if not notification.archived:
            notification.archived = True
            notification.archived_at = _utcnow()
            db.commit()
            db.refresh(notification)
        return notification


# Module-level singleton; stateless, so safe to share across requests.
notification_service = NotificationService()
