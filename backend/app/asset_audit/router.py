"""Asset Audit REST endpoints.

Thin by design: every endpoint validates input via Pydantic, resolves the
current principal / DB session via dependencies, delegates to
:data:`asset_audit_service`, and serialises the result. No business logic lives
here.

Mounted under ``/api/asset-audit`` so it never collides with the sibling
Activity-Log module's ``/api/audit`` routes.
"""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.asset_audit.deps import (
    Principal,
    Role,
    get_current_user,
    get_db,
    require_roles,
)
from app.asset_audit.models import AuditCycleStatus
from app.asset_audit.schemas import (
    AuditCycleCreate,
    AuditCycleRead,
    AuditCycleUpdate,
    AuditItemCreate,
    AuditItemRead,
    AuditItemVerify,
    AuditReport,
    Page,
    PageMeta,
)
from app.asset_audit.service import asset_audit_service

router = APIRouter(prefix="/api/asset-audit", tags=["Asset Audit"])

# Creating/updating/starting/closing cycles and enrolling assets are
# asset-manager (or admin) operations.
_manager_only = require_roles(Role.ASSET_MANAGER)


# --------------------------------------------------------------------------- #
# Audit cycle
# --------------------------------------------------------------------------- #
@router.post(
    "/cycle", response_model=AuditCycleRead, status_code=status.HTTP_201_CREATED
)
def create_cycle(
    payload: AuditCycleCreate,
    db: Session = Depends(get_db),
    current: Principal = Depends(_manager_only),
) -> AuditCycleRead:
    return AuditCycleRead.model_validate(
        asset_audit_service.create_cycle(db, current, payload)
    )


@router.get("/cycle", response_model=Page[AuditCycleRead])
def list_cycles(
    status_filter: Optional[AuditCycleStatus] = Query(None, alias="status"),
    department_id: Optional[str] = Query(None, min_length=1, max_length=64),
    search: Optional[str] = Query(None, description="Match against name/location"),
    sort_by: str = Query(
        "created_at",
        pattern="^(created_at|updated_at|start_date|end_date|status|name|id)$",
    ),
    order: str = Query("desc", pattern="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current: Principal = Depends(get_current_user),
) -> Page[AuditCycleRead]:
    items, total = asset_audit_service.list_cycles(
        db,
        current,
        status=status_filter,
        department_id=department_id,
        search=search,
        sort_by=sort_by,
        order=order,
        page=page,
        page_size=page_size,
    )
    return Page[AuditCycleRead](
        items=[AuditCycleRead.model_validate(c) for c in items],
        meta=PageMeta.build(total=total, page=page, page_size=page_size),
    )


@router.get("/cycle/{cycle_id}", response_model=AuditCycleRead)
def get_cycle(
    cycle_id: int,
    db: Session = Depends(get_db),
    current: Principal = Depends(get_current_user),
) -> AuditCycleRead:
    return AuditCycleRead.model_validate(
        asset_audit_service.get_cycle(db, current, cycle_id)
    )


@router.put("/cycle/{cycle_id}", response_model=AuditCycleRead)
def update_cycle(
    cycle_id: int,
    payload: AuditCycleUpdate,
    db: Session = Depends(get_db),
    current: Principal = Depends(_manager_only),
) -> AuditCycleRead:
    return AuditCycleRead.model_validate(
        asset_audit_service.update_cycle(db, current, cycle_id, payload)
    )


@router.post("/cycle/{cycle_id}/start", response_model=AuditCycleRead)
def start_cycle(
    cycle_id: int,
    db: Session = Depends(get_db),
    current: Principal = Depends(_manager_only),
) -> AuditCycleRead:
    return AuditCycleRead.model_validate(
        asset_audit_service.start_cycle(db, current, cycle_id)
    )


@router.post("/cycle/{cycle_id}/close", response_model=AuditCycleRead)
def close_cycle(
    cycle_id: int,
    db: Session = Depends(get_db),
    current: Principal = Depends(_manager_only),
) -> AuditCycleRead:
    return AuditCycleRead.model_validate(
        asset_audit_service.close_cycle(db, current, cycle_id)
    )


@router.get("/cycle/{cycle_id}/items", response_model=List[AuditItemRead])
def list_items(
    cycle_id: int,
    db: Session = Depends(get_db),
    current: Principal = Depends(get_current_user),
) -> List[AuditItemRead]:
    return [
        AuditItemRead.model_validate(i)
        for i in asset_audit_service.list_items(db, current, cycle_id)
    ]


# --------------------------------------------------------------------------- #
# Audit item
# --------------------------------------------------------------------------- #
@router.post(
    "/item", response_model=AuditItemRead, status_code=status.HTTP_201_CREATED
)
def add_item(
    payload: AuditItemCreate,
    db: Session = Depends(get_db),
    current: Principal = Depends(_manager_only),
) -> AuditItemRead:
    return AuditItemRead.model_validate(
        asset_audit_service.add_item(db, current, payload)
    )


@router.put("/item/{item_id}", response_model=AuditItemRead)
def verify_item(
    item_id: int,
    payload: AuditItemVerify,
    db: Session = Depends(get_db),
    current: Principal = Depends(get_current_user),
) -> AuditItemRead:
    return AuditItemRead.model_validate(
        asset_audit_service.verify_item(db, current, item_id, payload)
    )


# --------------------------------------------------------------------------- #
# Discrepancy report
# --------------------------------------------------------------------------- #
@router.get("/report/{cycle_id}", response_model=AuditReport)
def generate_report(
    cycle_id: int,
    db: Session = Depends(get_db),
    current: Principal = Depends(get_current_user),
) -> AuditReport:
    return asset_audit_service.generate_report(db, current, cycle_id)
