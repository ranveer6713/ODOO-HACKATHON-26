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

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.notifications import validators
from app.notifications.deps import Principal
from app.notifications.exceptions import NotFoundError, ValidationError
from app.notifications.models import Notification, NotificationType

_SORTABLE_FIELDS = {
    "created_at": Notification.created_at,
    "id": Notification.id,
    "is_read": Notification.is_read,
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
    ) -> Notification:
        """Deliver a notification to a single recipient.

        Called by sibling workflow services *inside their transaction*: this
        method never commits, so the message and the workflow mutation that
        triggered it are persisted together (or rolled back together).
        """
        recipient_id = validators.validate_recipient_id(recipient_id)
        validators.validate_content(title, message)

        notification = Notification(
            recipient_id=recipient_id,
            type=_coerce_type(type),
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
        type: Optional[Union[str, NotificationType]] = None,
        sort_by: str = "created_at",
        order: str = "desc",
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Notification], int]:
        conditions = [Notification.recipient_id == principal.id]
        if unread_only:
            conditions.append(Notification.is_read.is_(False))
        if type is not None:
            conditions.append(Notification.type == _coerce_type(type))

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
        """Mark every unread notification for the caller read; returns the count."""
        rows = list(
            db.execute(
                select(Notification).where(
                    Notification.recipient_id == principal.id,
                    Notification.is_read.is_(False),
                )
            )
            .scalars()
            .all()
        )
        now = _utcnow()
        for notification in rows:
            notification.is_read = True
            notification.read_at = now
        if rows:
            db.commit()
        return len(rows)


# Module-level singleton; stateless, so safe to share across requests.
notification_service = NotificationService()
