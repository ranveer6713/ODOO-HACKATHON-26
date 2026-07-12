"""Reports REST endpoints.

Thin by design: every endpoint resolves the current principal / DB session via
dependencies, delegates to :data:`reports_service`, and serialises the result.
No aggregation, export or business logic lives here.

The auth / session seam is consumed from :mod:`app.audit.deps` (the Activity Log
module) rather than re-declared — in production every module's seam resolves to
the same foundation ``get_db`` / ``get_current_user``, and this keeps Reports
free of a duplicated seam.

Route ordering matters: the literal ``/activity-log`` and ``/notifications``
routes are declared before the generic ``/{report_type}`` route so an enum path
converter never shadows them.
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from app.audit.deps import Principal, Role, get_current_user, get_db, require_roles
from app.audit.models import AuditSeverity
from app.audit.schemas import ActivityLogRead
from app.notifications.models import NotificationType
from app.notifications.schemas import MarkAllReadResult, NotificationRead, UnreadCount
from app.reports.schemas import (
    ExportFormat,
    NotificationView,
    Page,
    PageMeta,
    ReportCatalogEntry,
    ReportPage,
    ReportType,
)
from app.reports.service import reports_service

router = APIRouter(prefix="/api/reports", tags=["Reports"])

# Estate-wide reports are an operations view: asset managers (and admins, always).
_reports_access = require_roles(Role.ASSET_MANAGER)


def _collect_filters(
    *,
    status: Optional[str],
    priority: Optional[str],
    type: Optional[str],
    severity: Optional[str],
    department_id: Optional[str],
    asset_id: Optional[str],
    user_id: Optional[str],
    cycle_id: Optional[str],
) -> dict:
    """Bundle the generic filter query params; a report picks the ones it honours."""
    return {
        "status": status,
        "priority": priority,
        "type": type,
        "severity": severity,
        "department_id": department_id,
        "asset_id": asset_id,
        "user_id": user_id,
        "cycle_id": cycle_id,
    }


# ===========================================================================
# Catalogue
# ===========================================================================
@router.get("", response_model=List[ReportCatalogEntry])
def list_reports(
    current: Principal = Depends(_reports_access),
) -> List[ReportCatalogEntry]:
    return reports_service.catalog()


# ===========================================================================
# Activity Log UI backend (consumes the Activity Log service)
# ===========================================================================
@router.get("/activity-log", response_model=Page[ActivityLogRead])
def activity_log(
    search: Optional[str] = Query(None, description="Match action or description"),
    user_id: Optional[str] = Query(None, min_length=1, max_length=64, description="Actor filter"),
    action: Optional[str] = Query(None, min_length=1, max_length=64),
    entity_type: Optional[str] = Query(None, min_length=1, max_length=64),
    severity: Optional[AuditSeverity] = Query(None),
    date_from: Optional[datetime] = Query(None, description="Inclusive lower bound on timestamp"),
    date_to: Optional[datetime] = Query(None, description="Inclusive upper bound on timestamp"),
    sort_by: str = Query("created_at", pattern="^(created_at|severity|action|id)$"),
    order: str = Query("desc", pattern="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current: Principal = Depends(get_current_user),
) -> Page[ActivityLogRead]:
    items, total = reports_service.activity_log(
        db,
        current,
        search=search,
        actor_id=user_id,
        action=action,
        entity_type=entity_type,
        severity=severity,
        date_from=date_from,
        date_to=date_to,
        sort_by=sort_by,
        order=order,
        page=page,
        page_size=page_size,
    )
    return Page[ActivityLogRead](
        items=[ActivityLogRead.model_validate(e) for e in items],
        meta=PageMeta.build(total=total, page=page, page_size=page_size),
    )


# ===========================================================================
# Notifications UI backend (consumes the Notification service)
# ===========================================================================
@router.get("/notifications", response_model=Page[NotificationRead])
def list_notifications(
    view: NotificationView = Query(
        NotificationView.ALL, description="Inbox tab: all/unread/read/critical/archived"
    ),
    type: Optional[NotificationType] = Query(None),
    sort_by: str = Query("created_at", pattern="^(created_at|id|is_read|severity)$"),
    order: str = Query("desc", pattern="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current: Principal = Depends(get_current_user),
) -> Page[NotificationRead]:
    items, total = reports_service.notifications(
        db,
        current,
        unread_only=view is NotificationView.UNREAD,
        read_only=view is NotificationView.READ,
        critical_only=view is NotificationView.CRITICAL,
        type=type,
        archived=True if view is NotificationView.ARCHIVED else False,
        sort_by=sort_by,
        order=order,
        page=page,
        page_size=page_size,
    )
    return Page[NotificationRead](
        items=[NotificationRead.model_validate(n) for n in items],
        meta=PageMeta.build(total=total, page=page, page_size=page_size),
    )


@router.get("/notifications/unread-count", response_model=UnreadCount)
def notifications_unread_count(
    db: Session = Depends(get_db),
    current: Principal = Depends(get_current_user),
) -> UnreadCount:
    return UnreadCount(unread=reports_service.unread_count(db, current))


@router.post("/notifications/read-all", response_model=MarkAllReadResult)
def notifications_mark_all_read(
    db: Session = Depends(get_db),
    current: Principal = Depends(get_current_user),
) -> MarkAllReadResult:
    return MarkAllReadResult(
        marked_read=reports_service.mark_all_notifications_read(db, current)
    )


@router.post("/notifications/{notification_id}/read", response_model=NotificationRead)
def notifications_mark_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current: Principal = Depends(get_current_user),
) -> NotificationRead:
    return NotificationRead.model_validate(
        reports_service.mark_notification_read(db, current, notification_id)
    )


@router.post("/notifications/{notification_id}/archive", response_model=NotificationRead)
def notifications_archive(
    notification_id: int,
    db: Session = Depends(get_db),
    current: Principal = Depends(get_current_user),
) -> NotificationRead:
    return NotificationRead.model_validate(
        reports_service.archive_notification(db, current, notification_id)
    )


# ===========================================================================
# Reports (generic — declared last so it never shadows the literal routes)
# ===========================================================================
@router.get("/{report_type}", response_model=ReportPage)
def get_report(
    report_type: ReportType,
    search: Optional[str] = Query(None, description="Free-text search"),
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    department_id: Optional[str] = Query(None),
    asset_id: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    cycle_id: Optional[str] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    sort_by: Optional[str] = Query(None),
    order: str = Query("desc", pattern="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current: Principal = Depends(_reports_access),
) -> ReportPage:
    filters = _collect_filters(
        status=status, priority=priority, type=type, severity=severity,
        department_id=department_id, asset_id=asset_id, user_id=user_id, cycle_id=cycle_id,
    )
    try:
        return reports_service.run_report(
            db,
            report_type,
            search=search,
            filters=filters,
            date_from=date_from,
            date_to=date_to,
            sort_by=sort_by,
            order=order,
            page=page,
            page_size=page_size,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{report_type}/export")
def export_report(
    report_type: ReportType,
    format: ExportFormat = Query(ExportFormat.CSV, description="csv or pdf"),
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    department_id: Optional[str] = Query(None),
    asset_id: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    cycle_id: Optional[str] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    sort_by: Optional[str] = Query(None),
    order: str = Query("desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
    current: Principal = Depends(_reports_access),
) -> Response:
    filters = _collect_filters(
        status=status, priority=priority, type=type, severity=severity,
        department_id=department_id, asset_id=asset_id, user_id=user_id, cycle_id=cycle_id,
    )
    try:
        payload, media_type, filename = reports_service.export_report(
            db,
            report_type,
            format,
            search=search,
            filters=filters,
            date_from=date_from,
            date_to=date_to,
            sort_by=sort_by,
            order=order,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return Response(
        content=payload,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
