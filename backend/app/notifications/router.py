"""Notifications REST endpoints.

Thin by design: every endpoint resolves the current principal / DB session via
dependencies, delegates to :data:`notification_service`, and serialises the
result. No business logic lives here. Notifications are created by sibling
services through :meth:`NotificationService.notify`, so there is no create
endpoint — this surface is the recipient-facing inbox.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.notifications.deps import Principal, get_current_user, get_db
from app.notifications.models import NotificationType
from app.notifications.schemas import (
    MarkAllReadResult,
    NotificationRead,
    Page,
    PageMeta,
    UnreadCount,
)
from app.notifications.service import notification_service

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])


@router.get("", response_model=Page[NotificationRead])
def list_notifications(
    unread_only: bool = Query(False, description="Return only unread notifications"),
    type: Optional[NotificationType] = Query(None),
    sort_by: str = Query("created_at", pattern="^(created_at|id|is_read)$"),
    order: str = Query("desc", pattern="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current: Principal = Depends(get_current_user),
) -> Page[NotificationRead]:
    items, total = notification_service.list_for(
        db,
        current,
        unread_only=unread_only,
        type=type,
        sort_by=sort_by,
        order=order,
        page=page,
        page_size=page_size,
    )
    return Page[NotificationRead](
        items=[NotificationRead.model_validate(n) for n in items],
        meta=PageMeta.build(total=total, page=page, page_size=page_size),
    )


@router.get("/unread-count", response_model=UnreadCount)
def unread_count(
    db: Session = Depends(get_db),
    current: Principal = Depends(get_current_user),
) -> UnreadCount:
    return UnreadCount(unread=notification_service.unread_count(db, current))


@router.get("/{notification_id}", response_model=NotificationRead)
def get_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current: Principal = Depends(get_current_user),
) -> NotificationRead:
    return NotificationRead.model_validate(
        notification_service.get(db, current, notification_id)
    )


@router.post("/{notification_id}/read", response_model=NotificationRead)
def mark_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current: Principal = Depends(get_current_user),
) -> NotificationRead:
    return NotificationRead.model_validate(
        notification_service.mark_read(db, current, notification_id)
    )


@router.post("/read-all", response_model=MarkAllReadResult)
def mark_all_read(
    db: Session = Depends(get_db),
    current: Principal = Depends(get_current_user),
) -> MarkAllReadResult:
    return MarkAllReadResult(
        marked_read=notification_service.mark_all_read(db, current)
    )
