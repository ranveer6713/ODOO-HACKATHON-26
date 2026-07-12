"""Pydantic (v2) request/response schemas for the Asset Audit module."""
from __future__ import annotations

from datetime import date, datetime
from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.asset_audit.models import AuditCycleStatus, AuditItemStatus

T = TypeVar("T")


def _require_non_blank(value: str, field: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError(f"{field} must not be blank")
    return value


# --------------------------------------------------------------------------- #
# Audit cycle
# --------------------------------------------------------------------------- #
class AuditCycleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    department_id: Optional[str] = Field(None, max_length=64)
    location: Optional[str] = Field(None, max_length=255)
    start_date: date
    end_date: date

    @field_validator("name")
    @classmethod
    def _strip_name(cls, v: str) -> str:
        return _require_non_blank(v, "name")

    @field_validator("department_id", "location")
    @classmethod
    def _blank_to_none(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        return v or None


class AuditCycleUpdate(BaseModel):
    """Editable cycle metadata (only while the audit is not closed)."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    department_id: Optional[str] = Field(None, max_length=64)
    location: Optional[str] = Field(None, max_length=255)
    start_date: Optional[date] = None
    end_date: Optional[date] = None

    @field_validator("name")
    @classmethod
    def _strip_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return _require_non_blank(v, "name")


class AuditCycleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    department_id: Optional[str]
    location: Optional[str]
    start_date: date
    end_date: date
    created_by: str
    status: AuditCycleStatus
    started_at: Optional[datetime]
    closed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


# --------------------------------------------------------------------------- #
# Audit item
# --------------------------------------------------------------------------- #
class AuditItemCreate(BaseModel):
    """Enroll an asset in a cycle and assign an auditor to verify it."""

    audit_cycle_id: int = Field(..., ge=1)
    asset_id: str = Field(..., min_length=1, max_length=64)
    auditor_id: str = Field(..., min_length=1, max_length=64)

    @field_validator("asset_id")
    @classmethod
    def _strip_asset(cls, v: str) -> str:
        return _require_non_blank(v, "asset_id")

    @field_validator("auditor_id")
    @classmethod
    def _strip_auditor(cls, v: str) -> str:
        return _require_non_blank(v, "auditor_id")


class AuditItemVerify(BaseModel):
    """The auditor's verdict for an enrolled asset."""

    status: AuditItemStatus
    remarks: Optional[str] = Field(None, max_length=2000)

    @field_validator("remarks")
    @classmethod
    def _strip_remarks(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        return v or None


class AuditItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    audit_cycle_id: int
    asset_id: str
    auditor_id: str
    status: Optional[AuditItemStatus]
    remarks: Optional[str]
    verified_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


# --------------------------------------------------------------------------- #
# Discrepancy report
# --------------------------------------------------------------------------- #
class AuditReportSummary(BaseModel):
    total_items: int
    verified: int
    missing: int
    damaged: int
    pending: int


class AuditReport(BaseModel):
    cycle_id: int
    cycle_name: str
    status: AuditCycleStatus
    summary: AuditReportSummary
    discrepancy_count: int
    verified_assets: List[AuditItemRead]
    missing_assets: List[AuditItemRead]
    damaged_assets: List[AuditItemRead]


# --------------------------------------------------------------------------- #
# Pagination envelope
# --------------------------------------------------------------------------- #
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
