"""Pydantic (v2) request/response schemas for the Notifications module."""
from __future__ import annotations

from datetime import datetime
from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field

from app.notifications.models import NotificationSeverity, NotificationType

T = TypeVar("T")


class NotificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    recipient_id: str
    type: NotificationType
    severity: NotificationSeverity
    title: str
    message: str
    entity_type: Optional[str]
    entity_id: Optional[str]
    is_read: bool
    read_at: Optional[datetime]
    archived: bool
    archived_at: Optional[datetime]
    created_at: datetime


class UnreadCount(BaseModel):
    unread: int = Field(..., ge=0, description="Number of unread notifications")


class MarkAllReadResult(BaseModel):
    marked_read: int = Field(..., ge=0, description="How many were marked read")


class PageMeta(BaseModel):
    total: int = Field(..., description="Total number of matching records")
    page: int = Field(..., description="1-based current page")
    page_size: int = Field(..., description="Records per page")
    pages: int = Field(..., description="Total number of pages")

    @classmethod
    def build(cls, total: int, page: int, page_size: int) -> "PageMeta":
        pages = (total + page_size - 1) // page_size if page_size else 0
        return cls(total=total, page=page, page_size=page_size, pages=pages)


class Page(BaseModel, Generic[T]):
    """Generic paginated response envelope."""

    items: List[T]
    meta: PageMeta
