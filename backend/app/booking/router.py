"""Booking management REST endpoints.

Thin by design: every endpoint validates input via Pydantic, resolves the
current principal / DB session via dependencies, delegates to
:data:`booking_service`, and serialises the result. No business logic lives here.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.booking.deps import (
    Principal,
    Role,
    get_current_user,
    get_db,
    require_roles,
)
from app.booking.models import BookingStatus
from app.booking.schemas import (
    BookingCancel,
    BookingCreate,
    BookingRead,
    BookingReject,
    BookingUpdate,
    Page,
    PageMeta,
)
from app.booking.service import booking_service

router = APIRouter(prefix="/api/bookings", tags=["Bookings"])

# Approval / rejection are asset-manager (or admin) operations.
_manager_only = require_roles(Role.ASSET_MANAGER)


@router.post("", response_model=BookingRead, status_code=status.HTTP_201_CREATED)
def create_booking(
    payload: BookingCreate,
    db: Session = Depends(get_db),
    current: Principal = Depends(get_current_user),
) -> BookingRead:
    return BookingRead.model_validate(
        booking_service.create(db, current, payload)
    )


@router.get("", response_model=Page[BookingRead])
def list_bookings(
    status_filter: Optional[BookingStatus] = Query(None, alias="status"),
    asset_id: Optional[str] = Query(None, min_length=1, max_length=64),
    requested_by: Optional[str] = Query(None, min_length=1, max_length=64),
    search: Optional[str] = Query(None, description="Match against purpose"),
    sort_by: str = Query(
        "start_time",
        pattern="^(created_at|updated_at|start_time|end_time|status|id)$",
    ),
    order: str = Query("desc", pattern="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current: Principal = Depends(get_current_user),
) -> Page[BookingRead]:
    items, total = booking_service.list(
        db,
        current,
        status=status_filter,
        asset_id=asset_id,
        requested_by=requested_by,
        search=search,
        sort_by=sort_by,
        order=order,
        page=page,
        page_size=page_size,
    )
    return Page[BookingRead](
        items=[BookingRead.model_validate(b) for b in items],
        meta=PageMeta.build(total=total, page=page, page_size=page_size),
    )


@router.get("/{booking_id}", response_model=BookingRead)
def get_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current: Principal = Depends(get_current_user),
) -> BookingRead:
    return BookingRead.model_validate(
        booking_service.get(db, current, booking_id)
    )


@router.patch("/{booking_id}", response_model=BookingRead)
def update_booking(
    booking_id: int,
    payload: BookingUpdate,
    db: Session = Depends(get_db),
    current: Principal = Depends(get_current_user),
) -> BookingRead:
    return BookingRead.model_validate(
        booking_service.update(db, current, booking_id, payload)
    )


@router.delete("/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current: Principal = Depends(get_current_user),
) -> None:
    booking_service.delete(db, current, booking_id)


@router.post("/{booking_id}/approve", response_model=BookingRead)
def approve_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current: Principal = Depends(_manager_only),
) -> BookingRead:
    return BookingRead.model_validate(
        booking_service.approve(db, current, booking_id)
    )


@router.post("/{booking_id}/reject", response_model=BookingRead)
def reject_booking(
    booking_id: int,
    payload: BookingReject,
    db: Session = Depends(get_db),
    current: Principal = Depends(_manager_only),
) -> BookingRead:
    return BookingRead.model_validate(
        booking_service.reject(db, current, booking_id, payload.reason)
    )


@router.post("/{booking_id}/checkout", response_model=BookingRead)
def check_out_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current: Principal = Depends(get_current_user),
) -> BookingRead:
    return BookingRead.model_validate(
        booking_service.check_out(db, current, booking_id)
    )


@router.post("/{booking_id}/checkin", response_model=BookingRead)
def check_in_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current: Principal = Depends(get_current_user),
) -> BookingRead:
    return BookingRead.model_validate(
        booking_service.check_in(db, current, booking_id)
    )


@router.post("/{booking_id}/cancel", response_model=BookingRead)
def cancel_booking(
    booking_id: int,
    payload: BookingCancel = BookingCancel(),
    db: Session = Depends(get_db),
    current: Principal = Depends(get_current_user),
) -> BookingRead:
    return BookingRead.model_validate(
        booking_service.cancel(db, current, booking_id, payload.reason)
    )
