"""Pydantic (v2) schemas for the Reports module.

Reports is a read/aggregation layer (like the Dashboard): it exposes no request
bodies, only query parameters and response DTOs. Because a report's rows are
heterogeneous — the columns differ per report — a report row is modelled as a
plain ``dict`` of JSON-ready primitives keyed by the report's column keys. The
same row shape feeds the JSON response, the CSV export and the PDF export, so
there is a single source of truth for a report's contents.

Activity-log and notification *items* are not re-projected here: the router
returns the sibling modules' own read schemas (``ActivityLogRead`` /
``NotificationRead``), keeping this module free of duplicated DTOs.
"""
from __future__ import annotations

import enum
from typing import Any, Dict, Generic, List, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


# ---------------------------------------------------------------------------
# Pagination envelope (mirrors the sibling modules verbatim)
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Report enums
# ---------------------------------------------------------------------------
class ReportType(str, enum.Enum):
    """The catalogue of reports this module can render and export."""

    ASSET = "asset"
    BOOKING = "booking"
    MAINTENANCE = "maintenance"
    AUDIT = "audit"
    NOTIFICATION = "notification"
    DEPARTMENT = "department"


class ExportFormat(str, enum.Enum):
    CSV = "csv"
    PDF = "pdf"


class NotificationView(str, enum.Enum):
    """The notification inbox tabs the UI backend serves.

    ``ALL`` / ``UNREAD`` / ``READ`` / ``CRITICAL`` all scope to the *live* inbox
    (archived messages hidden); ``ARCHIVED`` shows the archive.
    """

    ALL = "all"
    UNREAD = "unread"
    READ = "read"
    CRITICAL = "critical"
    ARCHIVED = "archived"


# ---------------------------------------------------------------------------
# Report payloads
# ---------------------------------------------------------------------------
class ReportColumn(BaseModel):
    """One column in a report — a stable ``key`` and a human ``label``."""

    key: str
    label: str


class ReportPage(BaseModel):
    """A paginated slice of a report: its columns plus the rows on this page."""

    report: ReportType
    title: str
    columns: List[ReportColumn]
    items: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Rows keyed by column key; values are JSON-ready primitives",
    )
    meta: PageMeta


class ReportCatalogEntry(BaseModel):
    """Describes a single report so a UI can build its filter/sort controls."""

    report: ReportType
    title: str
    columns: List[ReportColumn]
    searchable: bool = Field(
        ..., description="Whether the report supports free-text search"
    )
    filters: List[str] = Field(
        default_factory=list, description="Filter fields this report honours"
    )
    sortable: List[str] = Field(
        default_factory=list, description="Fields this report can be sorted by"
    )
    default_sort: str = Field(..., description="Default sort field")
