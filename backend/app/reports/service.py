"""Reports aggregation, export, and UI-backend service.

Like the Dashboard, Reports is a **read-only presentation layer**: it owns no
tables, defines no business rule, and never mutates domain state except through
the sibling services that already own those rules. It has three jobs:

* **Reports** — six tabular reports (Asset, Booking, Maintenance, Audit,
  Notification, Department), each with search / filter / sort / pagination and
  CSV + PDF export. Every report produces one canonical row shape that feeds the
  JSON response *and* both exporters, so there is exactly one place a report's
  contents are computed.
* **Activity Log UI backend** — consumes :data:`app.audit.service.audit_service`
  (never re-queries ``activity_logs``) for a filtered, paginated, date-ranged,
  user/action-scoped feed.
* **Notifications UI backend** — consumes
  :data:`app.notifications.service.notification_service` for the recipient inbox
  (unread / read / critical / archived) and its mutations (mark read, mark all
  read, archive).

Design rules honoured throughout: optimized queries (filter/sort/paginate in the
database, one COUNT + one page query per read — never load-to-count), bulk
mutations delegated to the owning service, and no duplicated logic.
"""
from __future__ import annotations

import csv
import enum
import io
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple

from sqlalchemy import and_, case, func, inspect, or_, select, text
from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy.orm import InstrumentedAttribute, Session

from app.asset_audit.models import AuditCycle, AuditCycleStatus, AuditItem, AuditItemStatus
from app.audit.service import audit_service
from app.booking.models import Booking, BookingStatus
from app.maintenance.models import (
    MaintenancePriority,
    MaintenanceRequest,
    MaintenanceStatus,
)
from app.notifications.models import Notification, NotificationSeverity, NotificationType
from app.notifications.service import notification_service
from app.reports.schemas import (
    ExportFormat,
    PageMeta,
    ReportCatalogEntry,
    ReportColumn,
    ReportPage,
    ReportType,
)

# Hard ceiling on rows materialised into a single export, so an unbounded table
# can never exhaust memory. Reports beyond this are truncated to the newest rows.
EXPORT_MAX_ROWS = 10_000

# SQL errors that mean "the assets table/column isn't there" (SQLite / Postgres).
_MISSING_SCHEMA_ERRORS = (OperationalError, ProgrammingError)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _primitive(value: Any) -> Any:
    """Fold a model value into a JSON- and CSV-ready primitive.

    Enums collapse to their ``.value`` and datetimes to ISO-8601 strings so the
    JSON payload, the CSV export and the PDF export all render the same text.
    """
    if value is None:
        return None
    if isinstance(value, enum.Enum):  # covers str-subclass enums too
        return value.value
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def _enum_coercer(enum_cls) -> Callable[[str], Any]:
    """A coercer that turns a raw filter string into an enum (or raises)."""

    def coerce(raw: str):
        return enum_cls(raw)  # raises ValueError on an unknown member

    return coerce


def _identity(raw: str) -> str:
    return raw


# ===========================================================================
# ORM-backed report descriptors
# ===========================================================================
@dataclass(frozen=True)
class _OrmReport:
    """Declarative description of an ORM-backed tabular report.

    A single generic runner (:meth:`ReportsService._run_orm`) interprets this,
    so adding a report is data, not code. Column keys are model attribute names,
    which lets rows be serialised generically.
    """

    report: ReportType
    title: str
    model: Any
    columns: Tuple[Tuple[str, str], ...]  # (attr key, display label)
    search_attrs: Tuple[str, ...]
    filters: Dict[str, Tuple[InstrumentedAttribute, Callable[[str], Any]]]
    sort_attrs: Tuple[str, ...]
    default_sort: str
    date_attr: str

    def report_columns(self) -> List[ReportColumn]:
        return [ReportColumn(key=k, label=label) for k, label in self.columns]

    def serialize(self, obj: Any) -> Dict[str, Any]:
        return {key: _primitive(getattr(obj, key)) for key, _ in self.columns}


def _build_orm_reports() -> Dict[ReportType, _OrmReport]:
    return {
        ReportType.BOOKING: _OrmReport(
            report=ReportType.BOOKING,
            title="Booking Report",
            model=Booking,
            columns=(
                ("id", "ID"),
                ("asset_id", "Asset"),
                ("requested_by", "Requested By"),
                ("purpose", "Purpose"),
                ("status", "Status"),
                ("start_time", "Start"),
                ("end_time", "End"),
                ("approved_by", "Approved By"),
                ("created_at", "Created"),
            ),
            search_attrs=("purpose", "asset_id", "requested_by"),
            filters={
                "status": (Booking.status, _enum_coercer(BookingStatus)),
                "asset_id": (Booking.asset_id, _identity),
                "user_id": (Booking.requested_by, _identity),
            },
            sort_attrs=("id", "status", "start_time", "end_time", "created_at"),
            default_sort="created_at",
            date_attr="created_at",
        ),
        ReportType.MAINTENANCE: _OrmReport(
            report=ReportType.MAINTENANCE,
            title="Maintenance Report",
            model=MaintenanceRequest,
            columns=(
                ("id", "ID"),
                ("asset_id", "Asset"),
                ("raised_by", "Raised By"),
                ("priority", "Priority"),
                ("status", "Status"),
                ("issue_description", "Issue"),
                ("technician_id", "Technician"),
                ("created_at", "Created"),
                ("resolved_at", "Resolved"),
            ),
            search_attrs=("issue_description", "asset_id", "raised_by"),
            filters={
                "status": (MaintenanceRequest.status, _enum_coercer(MaintenanceStatus)),
                "priority": (
                    MaintenanceRequest.priority,
                    _enum_coercer(MaintenancePriority),
                ),
                "asset_id": (MaintenanceRequest.asset_id, _identity),
                "user_id": (MaintenanceRequest.raised_by, _identity),
            },
            sort_attrs=("id", "status", "priority", "created_at", "resolved_at"),
            default_sort="created_at",
            date_attr="created_at",
        ),
        ReportType.AUDIT: _OrmReport(
            report=ReportType.AUDIT,
            title="Audit Report",
            model=AuditItem,
            columns=(
                ("id", "ID"),
                ("audit_cycle_id", "Cycle"),
                ("asset_id", "Asset"),
                ("auditor_id", "Auditor"),
                ("status", "Verdict"),
                ("remarks", "Remarks"),
                ("verified_at", "Verified"),
                ("created_at", "Created"),
            ),
            search_attrs=("asset_id", "auditor_id", "remarks"),
            filters={
                "status": (AuditItem.status, _enum_coercer(AuditItemStatus)),
                "asset_id": (AuditItem.asset_id, _identity),
                "user_id": (AuditItem.auditor_id, _identity),
                "cycle_id": (AuditItem.audit_cycle_id, _identity),
            },
            sort_attrs=("id", "status", "verified_at", "created_at"),
            default_sort="created_at",
            date_attr="created_at",
        ),
        ReportType.NOTIFICATION: _OrmReport(
            report=ReportType.NOTIFICATION,
            title="Notification Report",
            model=Notification,
            columns=(
                ("id", "ID"),
                ("recipient_id", "Recipient"),
                ("type", "Type"),
                ("severity", "Severity"),
                ("title", "Title"),
                ("message", "Message"),
                ("is_read", "Read"),
                ("archived", "Archived"),
                ("created_at", "Created"),
            ),
            search_attrs=("title", "message", "recipient_id"),
            filters={
                "type": (Notification.type, _enum_coercer(NotificationType)),
                "severity": (
                    Notification.severity,
                    _enum_coercer(NotificationSeverity),
                ),
                "user_id": (Notification.recipient_id, _identity),
            },
            sort_attrs=("id", "type", "severity", "is_read", "created_at"),
            default_sort="created_at",
            date_attr="created_at",
        ),
    }


# ===========================================================================
# Read-only access to the foundation-owned ``assets`` table
# ===========================================================================
# Canonical asset columns the report reads, in display order. Only ``id`` and
# ``status`` are required; the rest are read only when the Asset module exposes
# them, so the report degrades gracefully instead of failing.
_ASSET_COLUMN_LABELS: Tuple[Tuple[str, str], ...] = (
    ("id", "Asset ID"),
    ("name", "Name"),
    ("status", "Status"),
    ("department_id", "Department"),
    ("category", "Category"),
)
_ASSET_FALLBACK_COLUMNS = ("id", "name", "status")
_ASSET_SORTABLE = frozenset({"id", "name", "status", "department_id", "category"})


class _AssetReader:
    """Read-only, schema-tolerant access to the shared ``assets`` table.

    Mirrors the Dashboard gateway's introspection discipline (never assume an
    optional column exists; degrade to empty when the table is absent) but adds
    row-level listing with search/filter/sort/pagination for the Asset Report.
    All identifiers are whitelisted against the real columns and all values are
    bound parameters, so no user input is ever interpolated into SQL.
    """

    def columns(self, db: Session) -> List[str]:
        try:
            inspector = inspect(db.connection())
            if not inspector.has_table("assets"):
                return []
            return [c["name"] for c in inspector.get_columns("assets")]
        except _MISSING_SCHEMA_ERRORS:  # pragma: no cover - defensive
            return []

    def _present(self, db: Session) -> List[str]:
        actual = set(self.columns(db))
        return [k for k, _ in _ASSET_COLUMN_LABELS if k in actual]

    def list_assets(
        self,
        db: Session,
        *,
        search: Optional[str],
        status: Optional[str],
        department_id: Optional[str],
        sort_by: str,
        order: str,
        page: int,
        page_size: int,
    ) -> Tuple[List[str], List[Dict[str, Any]], int]:
        present = self._present(db)
        if "id" not in present:
            # No assets table (or no usable schema): headers only, no rows.
            return list(_ASSET_FALLBACK_COLUMNS), [], 0

        available = set(present)
        clauses: List[str] = []
        params: Dict[str, Any] = {}

        if search and (search := search.strip()):
            like_cols = [c for c in ("id", "name") if c in available]
            if like_cols:
                clauses.append(
                    "(" + " OR ".join(f"{c} LIKE :q" for c in like_cols) + ")"
                )
                params["q"] = f"%{search}%"
        if status and "status" in available:
            clauses.append("status = :status")
            params["status"] = status
        if department_id and "department_id" in available:
            clauses.append("department_id = :dept")
            params["dept"] = department_id

        where_sql = f" WHERE {' AND '.join(clauses)}" if clauses else ""

        total = int(
            db.execute(
                text(f"SELECT COUNT(*) FROM assets{where_sql}"), params
            ).scalar_one()
        )

        sort_col = sort_by if sort_by in available and sort_by in _ASSET_SORTABLE else "id"
        direction = "DESC" if order.lower() == "desc" else "ASC"
        select_sql = ", ".join(present)
        rows = (
            db.execute(
                text(
                    f"SELECT {select_sql} FROM assets{where_sql} "
                    f"ORDER BY {sort_col} {direction}, id {direction} "
                    "LIMIT :limit OFFSET :offset"
                ),
                {**params, "limit": page_size, "offset": (page - 1) * page_size},
            )
            .mappings()
            .all()
        )
        return present, [dict(r) for r in rows], total

    def department_status_matrix(self, db: Session) -> Dict[str, Dict[str, int]]:
        """``{department: {status: count}}`` for assets, or ``{}`` if unsupported."""
        if "department_id" not in set(self.columns(db)):
            return {}
        try:
            rows = db.execute(
                text(
                    "SELECT COALESCE(department_id, 'Unassigned') AS dept, "
                    "status AS st, COUNT(*) AS c FROM assets GROUP BY dept, st"
                )
            ).all()
        except _MISSING_SCHEMA_ERRORS:  # pragma: no cover - defensive
            return {}
        matrix: Dict[str, Dict[str, int]] = {}
        for dept, st, count in rows:
            matrix.setdefault(str(dept), {})[str(st).strip().lower()] = int(count)
        return matrix


# ===========================================================================
# Department report columns
# ===========================================================================
_DEPARTMENT_COLUMNS: Tuple[Tuple[str, str], ...] = (
    ("department_id", "Department"),
    ("total_assets", "Total Assets"),
    ("available_assets", "Available"),
    ("under_maintenance_assets", "Under Maintenance"),
    ("audit_cycles", "Audit Cycles"),
    ("active_audit_cycles", "Active Cycles"),
)
_DEPARTMENT_SORTABLE = tuple(k for k, _ in _DEPARTMENT_COLUMNS)


class ReportsService:
    """Stateless orchestrator; the DB session and principal are passed per call."""

    def __init__(self, *, audit=audit_service, notifications=notification_service) -> None:
        self._orm_reports = _build_orm_reports()
        self._assets = _AssetReader()
        self._audit = audit
        self._notifications = notifications

    # ------------------------------------------------------------- catalogue
    def catalog(self) -> List[ReportCatalogEntry]:
        """Describe every report so a UI can build its filter/sort controls."""
        entries: List[ReportCatalogEntry] = []
        # Asset (Core-backed) report.
        entries.append(
            ReportCatalogEntry(
                report=ReportType.ASSET,
                title="Asset Report",
                columns=[ReportColumn(key=k, label=l) for k, l in _ASSET_COLUMN_LABELS],
                searchable=True,
                filters=["status", "department_id"],
                sortable=sorted(_ASSET_SORTABLE),
                default_sort="id",
            )
        )
        # ORM-backed reports, in the canonical order.
        for report in (
            ReportType.BOOKING,
            ReportType.MAINTENANCE,
            ReportType.AUDIT,
            ReportType.NOTIFICATION,
        ):
            spec = self._orm_reports[report]
            entries.append(
                ReportCatalogEntry(
                    report=report,
                    title=spec.title,
                    columns=spec.report_columns(),
                    searchable=bool(spec.search_attrs),
                    filters=list(spec.filters.keys()),
                    sortable=list(spec.sort_attrs),
                    default_sort=spec.default_sort,
                )
            )
        # Department (aggregate) report.
        entries.append(
            ReportCatalogEntry(
                report=ReportType.DEPARTMENT,
                title="Department Report",
                columns=[ReportColumn(key=k, label=l) for k, l in _DEPARTMENT_COLUMNS],
                searchable=True,
                filters=[],
                sortable=list(_DEPARTMENT_SORTABLE),
                default_sort="total_assets",
            )
        )
        return entries

    # ---------------------------------------------------------- report reads
    def run_report(
        self,
        db: Session,
        report: ReportType,
        *,
        search: Optional[str] = None,
        filters: Optional[Dict[str, Optional[str]]] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        sort_by: Optional[str] = None,
        order: str = "desc",
        page: int = 1,
        page_size: int = 20,
    ) -> ReportPage:
        """Render one paginated slice of a report."""
        title, columns, rows, total = self._collect(
            db,
            report,
            search=search,
            filters=filters or {},
            date_from=date_from,
            date_to=date_to,
            sort_by=sort_by,
            order=order,
            page=page,
            page_size=page_size,
        )
        return ReportPage(
            report=report,
            title=title,
            columns=columns,
            items=rows,
            meta=PageMeta.build(total=total, page=page, page_size=page_size),
        )

    def export_report(
        self,
        db: Session,
        report: ReportType,
        fmt: ExportFormat,
        *,
        search: Optional[str] = None,
        filters: Optional[Dict[str, Optional[str]]] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        sort_by: Optional[str] = None,
        order: str = "desc",
    ) -> Tuple[bytes, str, str]:
        """Render the full filtered report (capped) as CSV or PDF bytes.

        Returns ``(payload, media_type, filename)``. Export ignores pagination
        and materialises up to :data:`EXPORT_MAX_ROWS` rows of the same filtered,
        sorted result set the JSON report would return.
        """
        title, columns, rows, _ = self._collect(
            db,
            report,
            search=search,
            filters=filters or {},
            date_from=date_from,
            date_to=date_to,
            sort_by=sort_by,
            order=order,
            page=1,
            page_size=EXPORT_MAX_ROWS,
        )
        if fmt is ExportFormat.CSV:
            payload = render_csv(columns, rows)
            return payload, "text/csv", f"{report.value}-report.csv"
        payload = render_pdf(title, columns, rows)
        return payload, "application/pdf", f"{report.value}-report.pdf"

    # --------------------------------------------------------------- collect
    def _collect(
        self,
        db: Session,
        report: ReportType,
        *,
        search: Optional[str],
        filters: Dict[str, Optional[str]],
        date_from: Optional[datetime],
        date_to: Optional[datetime],
        sort_by: Optional[str],
        order: str,
        page: int,
        page_size: int,
    ) -> Tuple[str, List[ReportColumn], List[Dict[str, Any]], int]:
        """Dispatch to the right engine and return (title, columns, rows, total)."""
        if report is ReportType.ASSET:
            return self._collect_asset(
                db, search=search, filters=filters, sort_by=sort_by,
                order=order, page=page, page_size=page_size,
            )
        if report is ReportType.DEPARTMENT:
            return self._collect_department(
                db, search=search, sort_by=sort_by, order=order,
                page=page, page_size=page_size,
            )
        return self._run_orm(
            db,
            self._orm_reports[report],
            search=search,
            filters=filters,
            date_from=date_from,
            date_to=date_to,
            sort_by=sort_by,
            order=order,
            page=page,
            page_size=page_size,
        )

    def _run_orm(
        self,
        db: Session,
        spec: _OrmReport,
        *,
        search: Optional[str],
        filters: Dict[str, Optional[str]],
        date_from: Optional[datetime],
        date_to: Optional[datetime],
        sort_by: Optional[str],
        order: str,
        page: int,
        page_size: int,
    ) -> Tuple[str, List[ReportColumn], List[Dict[str, Any]], int]:
        conditions = []
        if search and search.strip():
            term = f"%{search.strip()}%"
            conditions.append(
                or_(*[getattr(spec.model, a).ilike(term) for a in spec.search_attrs])
            )
        for name, (column, coerce) in spec.filters.items():
            raw = filters.get(name)
            if raw is None or raw == "":
                continue
            try:
                conditions.append(column == coerce(raw))
            except ValueError as exc:
                raise ValueError(
                    f"Invalid value {raw!r} for filter {name!r}"
                ) from exc
        date_col = getattr(spec.model, spec.date_attr)
        if date_from is not None:
            conditions.append(date_col >= date_from)
        if date_to is not None:
            conditions.append(date_col <= date_to)

        where = and_(*conditions) if conditions else None

        count_q = select(func.count()).select_from(spec.model)
        if where is not None:
            count_q = count_q.where(where)
        total = int(db.execute(count_q).scalar_one())

        sort_attr = sort_by if sort_by in set(spec.sort_attrs) else spec.default_sort
        sort_col = getattr(spec.model, sort_attr)
        sort_col = sort_col.desc() if order.lower() == "desc" else sort_col.asc()
        pk = spec.model.id

        query = select(spec.model)
        if where is not None:
            query = query.where(where)
        query = (
            query.order_by(sort_col, pk.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        rows = [spec.serialize(o) for o in db.execute(query).scalars().all()]
        return spec.title, spec.report_columns(), rows, total

    def _collect_asset(
        self,
        db: Session,
        *,
        search: Optional[str],
        filters: Dict[str, Optional[str]],
        sort_by: Optional[str],
        order: str,
        page: int,
        page_size: int,
    ) -> Tuple[str, List[ReportColumn], List[Dict[str, Any]], int]:
        present, rows, total = self._assets.list_assets(
            db,
            search=search,
            status=filters.get("status"),
            department_id=filters.get("department_id"),
            sort_by=sort_by or "id",
            order=order,
            page=page,
            page_size=page_size,
        )
        labels = dict(_ASSET_COLUMN_LABELS)
        columns = [ReportColumn(key=k, label=labels.get(k, k.title())) for k in present]
        return "Asset Report", columns, rows, total

    def _collect_department(
        self,
        db: Session,
        *,
        search: Optional[str],
        sort_by: Optional[str],
        order: str,
        page: int,
        page_size: int,
    ) -> Tuple[str, List[ReportColumn], List[Dict[str, Any]], int]:
        matrix = self._assets.department_status_matrix(db)

        # Audit cycles per department (one grouped query over an owned table).
        active = func.coalesce(
            func.sum(case((AuditCycle.status == AuditCycleStatus.ACTIVE, 1), else_=0)),
            0,
        )
        dept_expr = func.coalesce(AuditCycle.department_id, "Unassigned")
        cycle_rows = db.execute(
            select(dept_expr, func.count(AuditCycle.id), active).group_by(dept_expr)
        ).all()
        cycle_map = {str(d): (int(c), int(a)) for d, c, a in cycle_rows}

        departments = sorted(set(matrix) | set(cycle_map))
        rows: List[Dict[str, Any]] = []
        for dept in departments:
            statuses = matrix.get(dept, {})
            total_assets = sum(statuses.values())
            cycles, active_cycles = cycle_map.get(dept, (0, 0))
            rows.append(
                {
                    "department_id": dept,
                    "total_assets": total_assets,
                    "available_assets": statuses.get("available", 0),
                    "under_maintenance_assets": (
                        statuses.get("under_maintenance", 0)
                        + statuses.get("maintenance", 0)
                    ),
                    "audit_cycles": cycles,
                    "active_audit_cycles": active_cycles,
                }
            )

        if search and (needle := search.strip().lower()):
            rows = [r for r in rows if needle in str(r["department_id"]).lower()]

        sort_key = sort_by if sort_by in _DEPARTMENT_SORTABLE else "total_assets"
        rows.sort(
            key=lambda r: (r[sort_key] is None, r[sort_key]),
            reverse=order.lower() == "desc",
        )

        total = len(rows)
        start = (page - 1) * page_size
        page_rows = rows[start : start + page_size]
        columns = [ReportColumn(key=k, label=l) for k, l in _DEPARTMENT_COLUMNS]
        return "Department Report", columns, page_rows, total

    # =================================================== Activity Log UI backend
    def activity_log(
        self,
        db: Session,
        principal,
        *,
        search: Optional[str] = None,
        actor_id: Optional[str] = None,
        action: Optional[str] = None,
        entity_type: Optional[str] = None,
        severity: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        sort_by: str = "created_at",
        order: str = "desc",
        page: int = 1,
        page_size: int = 20,
    ):
        """A filtered, paginated activity feed — consumes the Activity Log service.

        The RBAC scope (non-managers see only their own actions) and every filter
        live in :data:`audit_service`; this module adds none of that logic, it
        only forwards the UI's query.
        """
        return self._audit.list(
            db,
            principal,
            actor_id=actor_id,
            action=action,
            entity_type=entity_type,
            severity=severity,
            search=search,
            date_from=date_from,
            date_to=date_to,
            sort_by=sort_by,
            order=order,
            page=page,
            page_size=page_size,
        )

    # =================================================== Notifications UI backend
    def notifications(
        self,
        db: Session,
        principal,
        *,
        unread_only: bool = False,
        read_only: bool = False,
        critical_only: bool = False,
        type: Optional[NotificationType] = None,
        archived: Optional[bool] = None,
        sort_by: str = "created_at",
        order: str = "desc",
        page: int = 1,
        page_size: int = 20,
    ):
        """The recipient inbox — consumes the Notification service."""
        return self._notifications.list_for(
            db,
            principal,
            unread_only=unread_only,
            read_only=read_only,
            type=type,
            severity=NotificationSeverity.CRITICAL if critical_only else None,
            archived=archived,
            sort_by=sort_by,
            order=order,
            page=page,
            page_size=page_size,
        )

    def unread_count(self, db: Session, principal) -> int:
        return self._notifications.unread_count(db, principal)

    def mark_notification_read(self, db: Session, principal, notification_id: int):
        return self._notifications.mark_read(db, principal, notification_id)

    def mark_all_notifications_read(self, db: Session, principal) -> int:
        return self._notifications.mark_all_read(db, principal)

    def archive_notification(self, db: Session, principal, notification_id: int):
        return self._notifications.archive(db, principal, notification_id)


# Module-level singleton; stateless, so safe to share across requests.
reports_service = ReportsService()


# ===========================================================================
# Exporters — a report's rows render identically to CSV and PDF.
# ===========================================================================
def render_csv(columns: List[ReportColumn], rows: List[Dict[str, Any]]) -> bytes:
    """Serialise a report to RFC-4180 CSV (UTF-8), header row = column labels."""
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer)
    writer.writerow([c.label for c in columns])
    for row in rows:
        writer.writerow(["" if row.get(c.key) is None else row.get(c.key) for c in columns])
    return buffer.getvalue().encode("utf-8")


# --- Minimal, dependency-free PDF writer (Helvetica core fonts) -------------
_PDF_PAGE_W, _PDF_PAGE_H = 842, 595  # A4 landscape (points)
_PDF_MARGIN = 36
_PDF_FONT_SIZE = 8
_PDF_HEADER_SIZE = 9
_PDF_LINE_H = 13


def _pdf_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _pdf_cell(value: Any, max_chars: int) -> str:
    """Sanitise a value into a single, width-bounded, WinAnsi-safe PDF token."""
    text_value = "" if value is None else str(value)
    text_value = text_value.replace("\n", " ").replace("\r", " ").replace("\t", " ")
    # Core fonts are single-byte; drop anything outside latin-1 rather than fail.
    text_value = text_value.encode("latin-1", "replace").decode("latin-1")
    if len(text_value) > max_chars:
        text_value = text_value[: max(1, max_chars - 1)] + "."
    return _pdf_escape(text_value)


def render_pdf(title: str, columns: List[ReportColumn], rows: List[Dict[str, Any]]) -> bytes:
    """Render a report to a valid, self-contained single/multi-page PDF.

    Lays the columns out as an evenly-spaced table, paginating vertically and
    repeating the column header on every page. No third-party dependency: the
    bytes are a hand-assembled PDF-1.4 document with correct cross-references.
    """
    n = max(1, len(columns))
    content_w = _PDF_PAGE_W - 2 * _PDF_MARGIN
    col_w = content_w / n
    max_chars = max(4, int(col_w / (_PDF_FONT_SIZE * 0.5)))
    x_positions = [_PDF_MARGIN + i * col_w for i in range(n)]

    pages: List[str] = []
    ops: List[str] = []
    y = _PDF_PAGE_H - _PDF_MARGIN

    def draw(text_token: str, x: float, y_pos: float, size: int, bold: bool) -> None:
        font = "F2" if bold else "F1"
        ops.append(
            f"BT /{font} {size} Tf 1 0 0 1 {x:.2f} {y_pos:.2f} Tm ({text_token}) Tj ET"
        )

    def draw_header() -> None:
        nonlocal y
        for col, x in zip(columns, x_positions):
            draw(_pdf_cell(col.label, max_chars), x, y, _PDF_HEADER_SIZE, True)
        y -= 4
        ops.append(
            f"{_PDF_MARGIN:.2f} {y:.2f} m {_PDF_PAGE_W - _PDF_MARGIN:.2f} {y:.2f} l S"
        )
        y -= _PDF_LINE_H

    # Title band on the first page.
    draw(_pdf_cell(title, max_chars * n), _PDF_MARGIN, y, 14, True)
    y -= 22
    draw_header()

    for row in rows:
        if y < _PDF_MARGIN + _PDF_LINE_H:
            pages.append("\n".join(ops))
            ops = []
            y = _PDF_PAGE_H - _PDF_MARGIN
            draw_header()
        for col, x in zip(columns, x_positions):
            draw(_pdf_cell(row.get(col.key), max_chars), x, y, _PDF_FONT_SIZE, False)
        y -= _PDF_LINE_H
    pages.append("\n".join(ops))

    return _assemble_pdf(pages)


def _assemble_pdf(page_streams: List[str]) -> bytes:
    """Assemble page content streams into a valid PDF-1.4 byte string."""
    objects: List[bytes] = []  # object bodies (without the "N 0 obj" wrapper)

    # 1: Catalog, 2: Pages, 3: Helvetica, 4: Helvetica-Bold.
    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    page_count = len(page_streams)
    kids = " ".join(f"{5 + 2 * i} 0 R" for i in range(page_count))
    objects.append(
        f"<< /Type /Pages /Kids [{kids}] /Count {page_count} >>".encode("latin-1")
    )
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>")

    for i, stream in enumerate(page_streams):
        content_obj = 6 + 2 * i
        page_body = (
            f"<< /Type /Page /Parent 2 0 R "
            f"/MediaBox [0 0 {_PDF_PAGE_W} {_PDF_PAGE_H}] "
            f"/Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> "
            f"/Contents {content_obj} 0 R >>"
        ).encode("latin-1")
        objects.append(page_body)
        encoded = stream.encode("latin-1", "replace")
        content_body = (
            f"<< /Length {len(encoded)} >>\nstream\n".encode("latin-1")
            + encoded
            + b"\nendstream"
        )
        objects.append(content_body)

    out = bytearray(b"%PDF-1.4\n")
    offsets: List[int] = []
    for index, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{index} 0 obj\n".encode("latin-1") + body + b"\nendobj\n"

    xref_pos = len(out)
    count = len(objects) + 1
    out += f"xref\n0 {count}\n".encode("latin-1")
    out += b"0000000000 65535 f \n"
    for offset in offsets:
        out += f"{offset:010d} 00000 n \n".encode("latin-1")
    out += (
        f"trailer\n<< /Size {count} /Root 1 0 R >>\nstartxref\n{xref_pos}\n"
        "%%EOF\n"
    ).encode("latin-1")
    return bytes(out)
