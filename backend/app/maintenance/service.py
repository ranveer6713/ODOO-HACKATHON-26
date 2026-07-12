"""Maintenance management business logic and workflow orchestration.

The service is the only layer that mutates state. It coordinates:
    * the workflow state machine (delegated to :mod:`validators`),
    * asset interactions (delegated exclusively to :class:`AssetGateway`),
    * record-level access control, and
    * transaction boundaries (commit / rollback).

Routers stay thin by holding no logic of their own.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional, Tuple

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.audit.models import AuditSeverity
from app.audit.service import AuditService, audit_service
from app.maintenance import validators
from app.maintenance.deps import Principal, Role
from app.maintenance.exceptions import NotFoundError, PermissionDeniedError
from app.maintenance.gateway import AssetGateway, AssetStatus, asset_gateway
from app.maintenance.models import (
    MaintenancePriority,
    MaintenanceRequest,
    MaintenanceStatus,
)
from app.maintenance.schemas import MaintenanceCreate, MaintenanceUpdate
from app.notifications.models import NotificationType
from app.notifications.service import NotificationService, notification_service

_MANAGER_ROLES = (Role.ASSET_MANAGER, Role.ADMIN)

_ENTITY = "maintenance_request"

_SORTABLE_FIELDS = {
    "created_at": MaintenanceRequest.created_at,
    "updated_at": MaintenanceRequest.updated_at,
    "priority": MaintenanceRequest.priority,
    "status": MaintenanceRequest.status,
    "id": MaintenanceRequest.id,
}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class MaintenanceService:
    """Stateless orchestrator; the DB session is passed in per call."""

    def __init__(
        self,
        *,
        assets: Optional[AssetGateway] = None,
        activity_log: Optional[AuditService] = None,
        notifier: Optional[NotificationService] = None,
    ) -> None:
        # Dependency injection with sensible defaults; no global mutable state.
        self._assets = assets or asset_gateway
        self._activity_log = activity_log or audit_service
        self._notifier = notifier or notification_service

    # --------------------------------------------------------- cross-cutting
    def _log(
        self,
        db: Session,
        principal: Principal,
        request: MaintenanceRequest,
        action: str,
        description: str,
        severity: AuditSeverity = AuditSeverity.INFO,
    ) -> None:
        # Every workflow action creates an activity-log entry (participates in
        # this service's transaction; flushes but does not commit).
        self._activity_log.record(
            db,
            actor_id=principal.id,
            action=action,
            entity_type=_ENTITY,
            entity_id=str(request.id),
            description=description,
            severity=severity,
        )

    def _notify(
        self,
        db: Session,
        recipient_id: str,
        request: MaintenanceRequest,
        title: str,
        message: str,
    ) -> None:
        self._notifier.notify(
            db,
            recipient_id=recipient_id,
            type=NotificationType.MAINTENANCE,
            title=title,
            message=message,
            entity_type=_ENTITY,
            entity_id=str(request.id),
        )

    # ------------------------------------------------------------------ access
    def _is_manager(self, principal: Principal) -> bool:
        return principal.role in _MANAGER_ROLES

    def _visibility_filter(self, principal: Principal):
        """Non-managers only see requests they raised or are assigned to."""
        if self._is_manager(principal):
            return None
        return or_(
            MaintenanceRequest.raised_by == principal.id,
            MaintenanceRequest.technician_id == principal.id,
        )

    def _require(self, db: Session, request_id: int) -> MaintenanceRequest:
        request = db.get(MaintenanceRequest, request_id)
        if request is None:
            raise NotFoundError(f"Maintenance request {request_id} does not exist")
        return request

    def _ensure_technician(
        self, principal: Principal, request: MaintenanceRequest
    ) -> None:
        """Only the assigned technician (or an admin) may progress the work."""
        if principal.is_admin:
            return
        if request.technician_id is None or request.technician_id != principal.id:
            raise PermissionDeniedError(
                "Only the assigned technician can perform this action"
            )

    # ------------------------------------------------------------------- reads
    def get(
        self, db: Session, principal: Principal, request_id: int
    ) -> MaintenanceRequest:
        request = self._require(db, request_id)
        if not self._is_manager(principal):
            if principal.id not in (request.raised_by, request.technician_id):
                raise PermissionDeniedError(
                    "You are not allowed to view this maintenance request"
                )
        return request

    def list(
        self,
        db: Session,
        principal: Principal,
        *,
        status: Optional[MaintenanceStatus] = None,
        priority: Optional[MaintenancePriority] = None,
        asset_id: Optional[str] = None,
        technician_id: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: str = "created_at",
        order: str = "desc",
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[MaintenanceRequest], int]:
        conditions = []
        vis = self._visibility_filter(principal)
        if vis is not None:
            conditions.append(vis)
        if status is not None:
            conditions.append(MaintenanceRequest.status == status)
        if priority is not None:
            conditions.append(MaintenanceRequest.priority == priority)
        if asset_id is not None:
            conditions.append(MaintenanceRequest.asset_id == asset_id)
        if technician_id is not None:
            conditions.append(MaintenanceRequest.technician_id == technician_id)
        if search:
            conditions.append(
                MaintenanceRequest.issue_description.ilike(f"%{search.strip()}%")
            )

        where = and_(*conditions) if conditions else None

        count_query = select(func.count()).select_from(MaintenanceRequest)
        if where is not None:
            count_query = count_query.where(where)
        total = db.execute(count_query).scalar_one()

        column = _SORTABLE_FIELDS.get(sort_by, MaintenanceRequest.created_at)
        column = column.desc() if order.lower() == "desc" else column.asc()

        query = select(MaintenanceRequest)
        if where is not None:
            query = query.where(where)
        query = (
            query.order_by(column, MaintenanceRequest.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        rows = list(db.execute(query).scalars().all())
        return rows, total

    # --------------------------------------------------------------- lifecycle
    def create(
        self, db: Session, principal: Principal, data: MaintenanceCreate
    ) -> MaintenanceRequest:
        # Rule: disposed assets cannot enter maintenance (checked via gateway).
        self._assets.assert_maintainable(db, data.asset_id)

        request = MaintenanceRequest(
            asset_id=data.asset_id,
            raised_by=principal.id,
            priority=data.priority,
            issue_description=data.issue_description,
            photo_url=data.photo_url,
            status=MaintenanceStatus.PENDING,
        )
        db.add(request)
        db.flush()

        self._log(
            db, principal, request, "created",
            f"Maintenance request raised for asset {request.asset_id}",
        )
        self._notify(
            db, request.raised_by, request,
            "Maintenance request submitted",
            f"Your maintenance request for asset {request.asset_id} "
            "is pending approval.",
        )

        db.commit()
        db.refresh(request)
        return request

    def update(
        self,
        db: Session,
        principal: Principal,
        request_id: int,
        data: MaintenanceUpdate,
    ) -> MaintenanceRequest:
        request = self._require(db, request_id)
        if not self._is_manager(principal) and request.raised_by != principal.id:
            raise PermissionDeniedError(
                "Only the author or an asset manager can edit this request"
            )
        # Rule: resolved (and rejected) requests cannot be edited.
        validators.validate_editable(request)

        if data.priority is not None:
            request.priority = data.priority
        if data.issue_description is not None:
            request.issue_description = data.issue_description
        if data.photo_url is not None:
            request.photo_url = data.photo_url

        self._log(db, principal, request, "updated", "Maintenance request updated")
        db.commit()
        db.refresh(request)
        return request

    def delete(self, db: Session, principal: Principal, request_id: int) -> None:
        request = self._require(db, request_id)
        if not self._is_manager(principal) and request.raised_by != principal.id:
            raise PermissionDeniedError(
                "Only the author or an asset manager can delete this request"
            )
        self._log(
            db, principal, request, "deleted", "Maintenance request deleted",
            severity=AuditSeverity.WARNING,
        )
        db.delete(request)
        db.commit()

    def approve(
        self, db: Session, principal: Principal, request_id: int
    ) -> MaintenanceRequest:
        request = self._require(db, request_id)
        # Rule: cannot approve twice / only from pending.
        validators.validate_can_approve(request)

        request.status = MaintenanceStatus.APPROVED
        request.approved_by = principal.id
        request.approved_at = _utcnow()
        request.rejection_reason = None

        # Approval takes the asset out of service (asset interaction via gateway).
        self._assets.set_status(
            db, request.asset_id, AssetStatus.UNDER_MAINTENANCE
        )

        self._log(db, principal, request, "approved", "Maintenance request approved")
        self._notify(
            db, request.raised_by, request,
            "Maintenance request approved",
            f"Your maintenance request for asset {request.asset_id} was approved.",
        )

        db.commit()
        db.refresh(request)
        return request

    def reject(
        self, db: Session, principal: Principal, request_id: int, reason: str
    ) -> MaintenanceRequest:
        request = self._require(db, request_id)
        validators.validate_can_reject(request)

        request.status = MaintenanceStatus.REJECTED
        request.approved_by = principal.id
        request.rejection_reason = reason

        self._log(
            db, principal, request, "rejected",
            f"Maintenance request rejected: {reason}",
            severity=AuditSeverity.WARNING,
        )
        self._notify(
            db, request.raised_by, request,
            "Maintenance request rejected",
            f"Your maintenance request for asset {request.asset_id} "
            f"was rejected: {reason}",
        )

        db.commit()
        db.refresh(request)
        return request

    def assign_technician(
        self,
        db: Session,
        principal: Principal,
        request_id: int,
        technician_id: str,
    ) -> MaintenanceRequest:
        request = self._require(db, request_id)
        # Rule: cannot assign before approval.
        validators.validate_can_assign(request)

        request.technician_id = technician_id
        request.status = MaintenanceStatus.TECHNICIAN_ASSIGNED
        request.assigned_at = _utcnow()

        self._log(
            db, principal, request, "technician_assigned",
            f"Technician {technician_id} assigned",
        )
        self._notify(
            db, technician_id, request,
            "You have been assigned a maintenance job",
            f"You have been assigned to maintenance request {request.id} "
            f"for asset {request.asset_id}.",
        )

        db.commit()
        db.refresh(request)
        return request

    def start(
        self, db: Session, principal: Principal, request_id: int
    ) -> MaintenanceRequest:
        request = self._require(db, request_id)
        # Validate the transition first so an unassigned request yields the clear
        # "not assigned yet" error rather than a confusing permission error.
        validators.validate_can_start(request)
        self._ensure_technician(principal, request)

        request.status = MaintenanceStatus.IN_PROGRESS
        request.started_at = _utcnow()

        self._log(db, principal, request, "started", "Maintenance work started")
        self._notify(
            db, request.raised_by, request,
            "Maintenance work started",
            f"Work has started on your maintenance request for asset "
            f"{request.asset_id}.",
        )

        db.commit()
        db.refresh(request)
        return request

    def resolve(
        self,
        db: Session,
        principal: Principal,
        request_id: int,
        resolution_notes: str,
    ) -> MaintenanceRequest:
        request = self._require(db, request_id)
        # Rule: cannot resolve before In Progress (validated before the
        # assigned-technician permission check for a clearer error).
        validators.validate_can_resolve(request)
        self._ensure_technician(principal, request)

        request.status = MaintenanceStatus.RESOLVED
        request.resolved_at = _utcnow()
        request.resolution_notes = resolution_notes

        # Resolution returns the asset to service (asset interaction via gateway).
        self._assets.set_status(db, request.asset_id, AssetStatus.AVAILABLE)

        self._log(db, principal, request, "resolved", "Maintenance request resolved")
        self._notify(
            db, request.raised_by, request,
            "Maintenance request resolved",
            f"Your maintenance request for asset {request.asset_id} was resolved.",
        )

        db.commit()
        db.refresh(request)
        return request


# Module-level singleton; stateless, so safe to share.
maintenance_service = MaintenanceService()
