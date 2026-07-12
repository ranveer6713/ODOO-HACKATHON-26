"""Pydantic (v2) request/response schemas for the Booking module."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.booking.models import BookingStatus

T = TypeVar("T")


def _require_non_blank(value: str, field: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError(f"{field} must not be blank")
    return value


def _as_utc(value: datetime) -> datetime:
    """Normalise a datetime to timezone-aware UTC.

    Naive datetimes are interpreted as UTC so all stored/compared instants share
    one reference frame (SQLite has no native tz), which keeps overlap detection
    correct regardless of how a client expressed the instant.
    """
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


class BookingCreate(BaseModel):
    asset_id: str = Field(..., min_length=1, max_length=64)
    purpose: str = Field(..., min_length=1, max_length=2000)
    start_time: datetime
    end_time: datetime

    @field_validator("asset_id")
    @classmethod
    def _strip_asset_id(cls, v: str) -> str:
        return _require_non_blank(v, "asset_id")

    @field_validator("purpose")
    @classmethod
    def _strip_purpose(cls, v: str) -> str:
        return _require_non_blank(v, "purpose")

    @field_validator("start_time", "end_time")
    @classmethod
    def _normalise_tz(cls, v: datetime) -> datetime:
        return _as_utc(v)

    @model_validator(mode="after")
    def _check_window(self) -> "BookingCreate":
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        return self


class BookingUpdate(BaseModel):
    """Editable fields while the booking is still PENDING."""

    purpose: Optional[str] = Field(None, min_length=1, max_length=2000)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    @field_validator("purpose")
    @classmethod
    def _strip_purpose(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return _require_non_blank(v, "purpose")

    @field_validator("start_time", "end_time")
    @classmethod
    def _normalise_tz(cls, v: Optional[datetime]) -> Optional[datetime]:
        return _as_utc(v) if v is not None else v

    def has_changes(self) -> bool:
        return any(
            value is not None
            for value in (self.purpose, self.start_time, self.end_time)
        )


class BookingReject(BaseModel):
    reason: str = Field(..., min_length=1, max_length=1000)

    @field_validator("reason")
    @classmethod
    def _strip_reason(cls, v: str) -> str:
        return _require_non_blank(v, "reason")


class BookingCancel(BaseModel):
    reason: Optional[str] = Field(None, max_length=1000)

    @field_validator("reason")
    @classmethod
    def _strip_reason(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        return v or None


class BookingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    asset_id: str
    requested_by: str
    purpose: str
    start_time: datetime
    end_time: datetime
    status: BookingStatus
    approved_by: Optional[str]
    rejection_reason: Optional[str]
    cancelled_by: Optional[str]
    cancellation_reason: Optional[str]
    approved_at: Optional[datetime]
    checked_out_at: Optional[datetime]
    checked_in_at: Optional[datetime]
    cancelled_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


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
