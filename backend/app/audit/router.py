"""Audit (activity-log) REST endpoints.

Thin by design: endpoints resolve the current principal / DB session via
dependencies, delegate to :data:`audit_service`, and serialise the result. No
business logic lives here. There is no create endpoint — the trail is written by
sibling services through :meth:`AuditService.record`; this surface is read-only
plus the manager review lifecycle (flag / acknowledge).
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.audit.deps import Principal, Role, get_current_user, get_db, require_roles
from app.audit.models import AuditSeverity
from app.audit.schemas import (
    ActivityLogFlag,
    ActivityLogRead,
    Page,
    PageMeta,
)
from app.audit.service import audit_service

router = APIRouter(prefix="/api/audit", tags=["Audit"])

# Flagging is an asset-manager (or admin) operation.
_manager_only = require_roles(Role.ASSET_MANAGER)


@router.get("", response_model=Page[ActivityLogRead])
def list_activity(
    actor_id: Optional[str] = Query(None, min_length=1, max_length=64),
    action: Optional[str] = Query(None, min_length=1, max_length=64),
    entity_type: Optional[str] = Query(None, min_length=1, max_length=64),
    entity_id: Optional[str] = Query(None, min_length=1, max_length=64),
    severity: Optional[AuditSeverity] = Query(None),
    flagged: Optional[bool] = Query(None),
    search: Optional[str] = Query(None, description="Match action or description"),
    sort_by: str = Query(
        "created_at", pattern="^(created_at|severity|action|id)$"
    ),
    order: str = Query("desc", pattern="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current: Principal = Depends(get_current_user),
) -> Page[ActivityLogRead]:
    items, total = audit_service.list(
        db,
        current,
        actor_id=actor_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        severity=severity,
        flagged=flagged,
        search=search,
        sort_by=sort_by,
        order=order,
        page=page,
        page_size=page_size,
    )
    return Page[ActivityLogRead](
        items=[ActivityLogRead.model_validate(e) for e in items],
        meta=PageMeta.build(total=total, page=page, page_size=page_size),
    )


@router.get("/{entry_id}", response_model=ActivityLogRead)
def get_activity(
    entry_id: int,
    db: Session = Depends(get_db),
    current: Principal = Depends(get_current_user),
) -> ActivityLogRead:
    return ActivityLogRead.model_validate(
        audit_service.get(db, current, entry_id)
    )


@router.post("/{entry_id}/flag", response_model=ActivityLogRead)
def flag_activity(
    entry_id: int,
    payload: ActivityLogFlag,
    db: Session = Depends(get_db),
    current: Principal = Depends(_manager_only),
) -> ActivityLogRead:
    return ActivityLogRead.model_validate(
        audit_service.flag(db, current, entry_id, payload.reason)
    )


@router.post("/{entry_id}/acknowledge", response_model=ActivityLogRead)
def acknowledge_activity(
    entry_id: int,
    db: Session = Depends(get_db),
    current: Principal = Depends(get_current_user),
) -> ActivityLogRead:
    return ActivityLogRead.model_validate(
        audit_service.acknowledge(db, current, entry_id)
    )
