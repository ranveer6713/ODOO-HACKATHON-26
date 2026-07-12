"""Maintenance management REST endpoints.

Thin by design: every endpoint validates input via Pydantic, resolves the
current principal / DB session via dependencies, delegates to
:data:`maintenance_service`, and serialises the result. No business logic lives
here.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.maintenance.deps import (
    Principal,
    Role,
    get_current_user,
    get_db,
    require_roles,
)
from app.maintenance.models import MaintenancePriority, MaintenanceStatus
from app.maintenance.schemas import (
    MaintenanceCreate,
    MaintenanceRead,
    MaintenanceReject,
    MaintenanceResolve,
    MaintenanceUpdate,
    Page,
    PageMeta,
    TechnicianAssign,
)
from app.maintenance.service import maintenance_service

router = APIRouter(prefix="/api/maintenance", tags=["Maintenance"])

# Approval / rejection / assignment are asset-manager (or admin) operations.
_manager_only = require_roles(Role.ASSET_MANAGER)


@router.post("", response_model=MaintenanceRead, status_code=status.HTTP_201_CREATED)
def raise_request(
    payload: MaintenanceCreate,
    db: Session = Depends(get_db),
    current: Principal = Depends(get_current_user),
) -> MaintenanceRead:
    request = maintenance_service.create(db, current, payload)
    return MaintenanceRead.model_validate(request)


@router.get("", response_model=Page[MaintenanceRead])
def list_requests(
    status_filter: Optional[MaintenanceStatus] = Query(None, alias="status"),
    priority: Optional[MaintenancePriority] = Query(None),
    asset_id: Optional[str] = Query(None, min_length=1, max_length=64),
    technician_id: Optional[str] = Query(None, min_length=1, max_length=64),
    search: Optional[str] = Query(None, description="Match against issue description"),
    sort_by: str = Query(
        "created_at", pattern="^(created_at|updated_at|priority|status|id)$"
    ),
    order: str = Query("desc", pattern="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current: Principal = Depends(get_current_user),
) -> Page[MaintenanceRead]:
    items, total = maintenance_service.list(
        db,
        current,
        status=status_filter,
        priority=priority,
        asset_id=asset_id,
        technician_id=technician_id,
        search=search,
        sort_by=sort_by,
        order=order,
        page=page,
        page_size=page_size,
    )
    return Page[MaintenanceRead](
        items=[MaintenanceRead.model_validate(r) for r in items],
        meta=PageMeta.build(total=total, page=page, page_size=page_size),
    )


@router.get("/{request_id}", response_model=MaintenanceRead)
def get_request(
    request_id: int,
    db: Session = Depends(get_db),
    current: Principal = Depends(get_current_user),
) -> MaintenanceRead:
    return MaintenanceRead.model_validate(
        maintenance_service.get(db, current, request_id)
    )


@router.patch("/{request_id}", response_model=MaintenanceRead)
def update_request(
    request_id: int,
    payload: MaintenanceUpdate,
    db: Session = Depends(get_db),
    current: Principal = Depends(get_current_user),
) -> MaintenanceRead:
    return MaintenanceRead.model_validate(
        maintenance_service.update(db, current, request_id, payload)
    )


@router.delete("/{request_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_request(
    request_id: int,
    db: Session = Depends(get_db),
    current: Principal = Depends(get_current_user),
) -> None:
    maintenance_service.delete(db, current, request_id)


@router.post("/{request_id}/approve", response_model=MaintenanceRead)
def approve_request(
    request_id: int,
    db: Session = Depends(get_db),
    current: Principal = Depends(_manager_only),
) -> MaintenanceRead:
    return MaintenanceRead.model_validate(
        maintenance_service.approve(db, current, request_id)
    )


@router.post("/{request_id}/reject", response_model=MaintenanceRead)
def reject_request(
    request_id: int,
    payload: MaintenanceReject,
    db: Session = Depends(get_db),
    current: Principal = Depends(_manager_only),
) -> MaintenanceRead:
    return MaintenanceRead.model_validate(
        maintenance_service.reject(db, current, request_id, payload.reason)
    )


@router.post("/{request_id}/assign", response_model=MaintenanceRead)
def assign_technician(
    request_id: int,
    payload: TechnicianAssign,
    db: Session = Depends(get_db),
    current: Principal = Depends(_manager_only),
) -> MaintenanceRead:
    return MaintenanceRead.model_validate(
        maintenance_service.assign_technician(
            db, current, request_id, payload.technician_id
        )
    )


@router.post("/{request_id}/start", response_model=MaintenanceRead)
def start_request(
    request_id: int,
    db: Session = Depends(get_db),
    current: Principal = Depends(get_current_user),
) -> MaintenanceRead:
    return MaintenanceRead.model_validate(
        maintenance_service.start(db, current, request_id)
    )


@router.post("/{request_id}/resolve", response_model=MaintenanceRead)
def resolve_request(
    request_id: int,
    payload: MaintenanceResolve,
    db: Session = Depends(get_db),
    current: Principal = Depends(get_current_user),
) -> MaintenanceRead:
    return MaintenanceRead.model_validate(
        maintenance_service.resolve(db, current, request_id, payload.resolution_notes)
    )
