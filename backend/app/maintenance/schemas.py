"""Pydantic (v2) request/response schemas for the Maintenance module."""
from __future__ import annotations

from datetime import datetime
from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.maintenance.models import MaintenancePriority, MaintenanceStatus

T = TypeVar("T")


def _require_non_blank(value: str, field: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError(f"{field} must not be blank")
    return value


class MaintenanceCreate(BaseModel):
    asset_id: str = Field(..., min_length=1, max_length=64)
    priority: MaintenancePriority = MaintenancePriority.MEDIUM
    issue_description: str = Field(..., min_length=1)
    photo_url: Optional[str] = Field(None, max_length=1024)

    @field_validator("asset_id")
    @classmethod
    def _strip_asset_id(cls, v: str) -> str:
        return _require_non_blank(v, "asset_id")

    @field_validator("issue_description")
    @classmethod
    def _strip_description(cls, v: str) -> str:
        return _require_non_blank(v, "issue_description")


class MaintenanceUpdate(BaseModel):
    """Editable fields while the request has not yet been resolved/rejected."""

    priority: Optional[MaintenancePriority] = None
    issue_description: Optional[str] = Field(None, min_length=1)
    photo_url: Optional[str] = Field(None, max_length=1024)

    @field_validator("issue_description")
    @classmethod
    def _strip_description(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return _require_non_blank(v, "issue_description")


class MaintenanceReject(BaseModel):
    reason: str = Field(..., min_length=1, max_length=1000)

    @field_validator("reason")
    @classmethod
    def _strip_reason(cls, v: str) -> str:
        return _require_non_blank(v, "reason")


class TechnicianAssign(BaseModel):
    technician_id: str = Field(..., min_length=1, max_length=64)

    @field_validator("technician_id")
    @classmethod
    def _strip_technician(cls, v: str) -> str:
        return _require_non_blank(v, "technician_id")


class MaintenanceResolve(BaseModel):
    resolution_notes: str = Field(..., min_length=1, max_length=2000)

    @field_validator("resolution_notes")
    @classmethod
    def _strip_notes(cls, v: str) -> str:
        return _require_non_blank(v, "resolution_notes")


class MaintenanceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    asset_id: str
    raised_by: str
    priority: MaintenancePriority
    issue_description: str
    photo_url: Optional[str]
    status: MaintenanceStatus
    approved_by: Optional[str]
    technician_id: Optional[str]
    rejection_reason: Optional[str]
    resolution_notes: Optional[str]
    approved_at: Optional[datetime]
    assigned_at: Optional[datetime]
    started_at: Optional[datetime]
    resolved_at: Optional[datetime]
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
