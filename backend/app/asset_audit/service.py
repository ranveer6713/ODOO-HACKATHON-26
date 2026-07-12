"""Asset Audit business logic and workflow orchestration.

The service is the only layer that mutates state. It coordinates:
    * the cycle state machine (delegated to :mod:`validators`),
    * asset interactions (delegated exclusively to :class:`AssetGateway` — the
      Asset ORM model is never imported),
    * record-level access control,
    * discrepancy-report generation,
    * the shared activity-log and notification ports, and
    * transaction boundaries (commit / rollback).

Routers stay thin by holding no logic of their own.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional, Tuple

from sqlalchemy import and_, exists, func, or_, select
from sqlalchemy.orm import Session

from app.asset_audit import validators
from app.asset_audit.deps import Principal, Role
from app.asset_audit.exceptions import NotFoundError, PermissionDeniedError
from app.asset_audit.gateway import AssetGateway, asset_gateway
from app.asset_audit.models import (
    AuditCycle,
    AuditCycleStatus,
    AuditItem,
    AuditItemStatus,
    DISCREPANCY_STATUSES,
)
from app.asset_audit.schemas import (
    AuditCycleCreate,
    AuditCycleUpdate,
    AuditItemCreate,
    AuditItemVerify,
    AuditReport,
    AuditReportSummary,
)

# The audit trail and notification ports are shared foundation services. We
# depend only on their public interfaces (record / notify).
from app.audit.models import AuditSeverity
from app.audit.service import AuditService, audit_service
from app.notifications.models import NotificationType
from app.notifications.service import NotificationService, notification_service

_MANAGER_ROLES = (Role.ASSET_MANAGER, Role.ADMIN)

_ENTITY_CYCLE = "audit_cycle"
_ENTITY_ITEM = "audit_item"

_CYCLE_SORTABLE_FIELDS = {
    "created_at": AuditCycle.created_at,
    "updated_at": AuditCycle.updated_at,
    "start_date": AuditCycle.start_date,
    "end_date": AuditCycle.end_date,
    "status": AuditCycle.status,
    "name": AuditCycle.name,
    "id": AuditCycle.id,
}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AssetAuditService:
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
        *,
        action: str,
        entity_type: str,
        entity_id: int,
        description: str,
        severity: AuditSeverity = AuditSeverity.INFO,
    ) -> None:
        # Every workflow action creates an activity-log entry (participates in
        # this service's transaction; flushes but does not commit).
        self._activity_log.record(
            db,
            actor_id=principal.id,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id),
            description=description,
            severity=severity,
        )

    def _notify(
        self,
        db: Session,
        *,
        recipient_id: str,
        cycle_id: int,
        title: str,
        message: str,
    ) -> None:
        self._notifier.notify(
            db,
            recipient_id=recipient_id,
            type=NotificationType.AUDIT,
            title=title,
            message=message,
            entity_type=_ENTITY_CYCLE,
            entity_id=str(cycle_id),
        )

    # ------------------------------------------------------------------ access
    def _is_manager(self, principal: Principal) -> bool:
        return principal.role in _MANAGER_ROLES

    def _require_cycle(self, db: Session, cycle_id: int) -> AuditCycle:
        cycle = db.get(AuditCycle, cycle_id)
        if cycle is None:
            raise NotFoundError(f"Audit cycle {cycle_id} does not exist")
        return cycle

    def _require_item(self, db: Session, item_id: int) -> AuditItem:
        item = db.get(AuditItem, item_id)
        if item is None:
            raise NotFoundError(f"Audit item {item_id} does not exist")
        return item

    def _is_auditor_in_cycle(
        self, db: Session, principal: Principal, cycle_id: int
    ) -> bool:
        return bool(
            db.execute(
                select(
                    exists().where(
                        and_(
                            AuditItem.audit_cycle_id == cycle_id,
                            AuditItem.auditor_id == principal.id,
                        )
                    )
                )
            ).scalar()
        )

    def _ensure_can_view_cycle(
        self, db: Session, principal: Principal, cycle: AuditCycle
    ) -> None:
        """Managers/admins see every cycle; others only cycles they audit."""
        if self._is_manager(principal):
            return
        if not self._is_auditor_in_cycle(db, principal, cycle.id):
            raise PermissionDeniedError(
                "You are not allowed to view this audit cycle"
            )

    def _distinct_auditor_ids(self, db: Session, cycle_id: int) -> List[str]:
        return list(
            db.execute(
                select(AuditItem.auditor_id)
                .where(AuditItem.audit_cycle_id == cycle_id)
                .distinct()
            )
            .scalars()
            .all()
        )

    def _items_for(self, db: Session, cycle_id: int) -> List[AuditItem]:
        return list(
            db.execute(
                select(AuditItem)
                .where(AuditItem.audit_cycle_id == cycle_id)
                .order_by(AuditItem.id.asc())
            )
            .scalars()
            .all()
        )

    # =========================================================== cycle: writes
    def create_cycle(
        self, db: Session, principal: Principal, data: AuditCycleCreate
    ) -> AuditCycle:
        validators.validate_dates(data.start_date, data.end_date)

        cycle = AuditCycle(
            name=data.name,
            department_id=data.department_id,
            location=data.location,
            start_date=data.start_date,
            end_date=data.end_date,
            created_by=principal.id,
            status=AuditCycleStatus.CREATED,
        )
        db.add(cycle)
        db.flush()

        self._log(
            db, principal,
            action="created",
            entity_type=_ENTITY_CYCLE,
            entity_id=cycle.id,
            description=f"Audit cycle '{cycle.name}' created",
        )

        db.commit()
        db.refresh(cycle)
        return cycle

    def update_cycle(
        self,
        db: Session,
        principal: Principal,
        cycle_id: int,
        data: AuditCycleUpdate,
    ) -> AuditCycle:
        cycle = self._require_cycle(db, cycle_id)
        # Rule: a closed audit cannot be edited.
        validators.validate_cycle_editable(cycle)

        new_start = data.start_date if data.start_date is not None else cycle.start_date
        new_end = data.end_date if data.end_date is not None else cycle.end_date
        validators.validate_dates(new_start, new_end)

        if data.name is not None:
            cycle.name = data.name
        if data.department_id is not None:
            cycle.department_id = data.department_id
        if data.location is not None:
            cycle.location = data.location
        if data.start_date is not None:
            cycle.start_date = data.start_date
        if data.end_date is not None:
            cycle.end_date = data.end_date

        self._log(
            db, principal,
            action="updated",
            entity_type=_ENTITY_CYCLE,
            entity_id=cycle.id,
            description=f"Audit cycle '{cycle.name}' updated",
        )

        db.commit()
        db.refresh(cycle)
        return cycle

    def start_cycle(
        self, db: Session, principal: Principal, cycle_id: int
    ) -> AuditCycle:
        cycle = self._require_cycle(db, cycle_id)
        # Rule: only a created cycle can be started (once).
        validators.validate_can_start(cycle)

        cycle.status = AuditCycleStatus.ACTIVE
        cycle.started_at = _utcnow()

        self._log(
            db, principal,
            action="started",
            entity_type=_ENTITY_CYCLE,
            entity_id=cycle.id,
            description=f"Audit cycle '{cycle.name}' started",
        )
        # Notify every assigned auditor that the audit has begun.
        for auditor_id in self._distinct_auditor_ids(db, cycle.id):
            self._notify(
                db,
                recipient_id=auditor_id,
                cycle_id=cycle.id,
                title="Audit started",
                message=(
                    f"Audit cycle '{cycle.name}' has started. "
                    "Please verify your assigned assets."
                ),
            )

        db.commit()
        db.refresh(cycle)
        return cycle

    def close_cycle(
        self, db: Session, principal: Principal, cycle_id: int
    ) -> AuditCycle:
        cycle = self._require_cycle(db, cycle_id)
        items = self._items_for(db, cycle.id)
        # Rules: cannot close an empty audit; only an active audit can be closed.
        validators.validate_can_close(cycle, len(items))

        report = self._build_report(cycle, items)

        # Confirmed-missing assets are transitioned to LOST via the gateway.
        for item in items:
            if item.status == AuditItemStatus.MISSING:
                self._assets.mark_lost(db, item.asset_id)

        cycle.status = AuditCycleStatus.CLOSED
        cycle.closed_at = _utcnow()

        severity = (
            AuditSeverity.WARNING
            if report.discrepancy_count > 0
            else AuditSeverity.INFO
        )
        self._log(
            db, principal,
            action="closed",
            entity_type=_ENTITY_CYCLE,
            entity_id=cycle.id,
            description=(
                f"Audit cycle '{cycle.name}' closed with "
                f"{report.discrepancy_count} discrepancy(ies)"
            ),
            severity=severity,
        )

        # Notify the owner and every auditor that the cycle is closed; raise a
        # discrepancy alert when the report is not clean. Auditor ids are derived
        # from the already-loaded items, avoiding a redundant round-trip.
        recipients = {cycle.created_by, *(item.auditor_id for item in items)}
        for recipient_id in recipients:
            self._notify(
                db,
                recipient_id=recipient_id,
                cycle_id=cycle.id,
                title="Audit closed",
                message=f"Audit cycle '{cycle.name}' has been closed.",
            )
        if report.discrepancy_count > 0:
            self._notify(
                db,
                recipient_id=cycle.created_by,
                cycle_id=cycle.id,
                title="Audit discrepancies found",
                message=(
                    f"Audit cycle '{cycle.name}' closed with "
                    f"{report.summary.missing} missing and "
                    f"{report.summary.damaged} damaged asset(s)."
                ),
            )

        db.commit()
        db.refresh(cycle)
        return cycle

    # ============================================================ cycle: reads
    def get_cycle(
        self, db: Session, principal: Principal, cycle_id: int
    ) -> AuditCycle:
        cycle = self._require_cycle(db, cycle_id)
        self._ensure_can_view_cycle(db, principal, cycle)
        return cycle

    def list_cycles(
        self,
        db: Session,
        principal: Principal,
        *,
        status: Optional[AuditCycleStatus] = None,
        department_id: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: str = "created_at",
        order: str = "desc",
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[AuditCycle], int]:
        conditions = []
        # Non-managers only see cycles they are an auditor on.
        if not self._is_manager(principal):
            conditions.append(
                exists().where(
                    and_(
                        AuditItem.audit_cycle_id == AuditCycle.id,
                        AuditItem.auditor_id == principal.id,
                    )
                )
            )
        if status is not None:
            conditions.append(AuditCycle.status == status)
        if department_id is not None:
            conditions.append(AuditCycle.department_id == department_id)
        if search:
            term = f"%{search.strip()}%"
            conditions.append(
                or_(
                    AuditCycle.name.ilike(term),
                    AuditCycle.location.ilike(term),
                )
            )

        where = and_(*conditions) if conditions else None

        count_query = select(func.count()).select_from(AuditCycle)
        if where is not None:
            count_query = count_query.where(where)
        total = db.execute(count_query).scalar_one()

        column = _CYCLE_SORTABLE_FIELDS.get(sort_by, AuditCycle.created_at)
        column = column.desc() if order.lower() == "desc" else column.asc()

        query = select(AuditCycle)
        if where is not None:
            query = query.where(where)
        query = (
            query.order_by(column, AuditCycle.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        rows = list(db.execute(query).scalars().all())
        return rows, total

    def list_items(
        self, db: Session, principal: Principal, cycle_id: int
    ) -> List[AuditItem]:
        cycle = self._require_cycle(db, cycle_id)
        self._ensure_can_view_cycle(db, principal, cycle)
        return self._items_for(db, cycle.id)

    # ============================================================ item: writes
    def add_item(
        self, db: Session, principal: Principal, data: AuditItemCreate
    ) -> AuditItem:
        cycle = self._require_cycle(db, data.audit_cycle_id)
        # Rule: cannot modify a closed audit.
        validators.validate_can_add_item(cycle)

        # The asset must exist (checked via the gateway, never the ORM model).
        self._assets.require(db, data.asset_id)

        # Rules: one asset once per cycle; no duplicate auditor entry.
        existing = db.execute(
            select(AuditItem).where(
                and_(
                    AuditItem.audit_cycle_id == cycle.id,
                    AuditItem.asset_id == data.asset_id,
                )
            )
        ).scalar_one_or_none()
        validators.validate_no_duplicate(existing, data.asset_id, data.auditor_id)

        item = AuditItem(
            audit_cycle_id=cycle.id,
            asset_id=data.asset_id,
            auditor_id=data.auditor_id,
            status=None,
        )
        db.add(item)
        db.flush()

        self._log(
            db, principal,
            action="auditor_assigned",
            entity_type=_ENTITY_ITEM,
            entity_id=item.id,
            description=(
                f"Auditor {item.auditor_id} assigned to asset "
                f"{item.asset_id} in audit cycle {cycle.id}"
            ),
        )
        # Notify the assigned auditor.
        self._notify(
            db,
            recipient_id=item.auditor_id,
            cycle_id=cycle.id,
            title="You have been assigned as an auditor",
            message=(
                f"You have been assigned to verify asset {item.asset_id} "
                f"in audit cycle '{cycle.name}'."
            ),
        )

        db.commit()
        db.refresh(item)
        return item

    def verify_item(
        self,
        db: Session,
        principal: Principal,
        item_id: int,
        data: AuditItemVerify,
    ) -> AuditItem:
        item = self._require_item(db, item_id)
        cycle = self._require_cycle(db, item.audit_cycle_id)

        # Only the assigned auditor (or an admin) may record a verdict.
        if not principal.is_admin and item.auditor_id != principal.id:
            raise PermissionDeniedError(
                "Only the assigned auditor can verify this asset"
            )
        # Rules: cannot verify a closed/not-started cycle; cannot verify twice.
        validators.validate_item_verifiable(item, cycle)

        item.status = data.status
        item.remarks = data.remarks
        item.verified_at = _utcnow()

        is_discrepancy = item.status in DISCREPANCY_STATUSES
        self._log(
            db, principal,
            action="verified",
            entity_type=_ENTITY_ITEM,
            entity_id=item.id,
            description=(
                f"Asset {item.asset_id} marked {item.status.value}"
                + (f": {item.remarks}" if item.remarks else "")
            ),
            severity=AuditSeverity.WARNING if is_discrepancy else AuditSeverity.INFO,
        )
        # A discrepancy alerts the cycle owner immediately.
        if is_discrepancy:
            self._notify(
                db,
                recipient_id=cycle.created_by,
                cycle_id=cycle.id,
                title="Audit discrepancy found",
                message=(
                    f"Asset {item.asset_id} was marked {item.status.value} "
                    f"in audit cycle '{cycle.name}'."
                ),
            )

        db.commit()
        db.refresh(item)
        return item

    # =============================================================== reporting
    def generate_report(
        self, db: Session, principal: Principal, cycle_id: int
    ) -> AuditReport:
        cycle = self._require_cycle(db, cycle_id)
        self._ensure_can_view_cycle(db, principal, cycle)
        items = self._items_for(db, cycle.id)
        return self._build_report(cycle, items)

    def _build_report(
        self, cycle: AuditCycle, items: List[AuditItem]
    ) -> AuditReport:
        """Assemble the discrepancy report from a cycle's items (pure function)."""
        # Import here to avoid a schema<->model import cycle at module load.
        from app.asset_audit.schemas import AuditItemRead

        verified = [i for i in items if i.status == AuditItemStatus.VERIFIED]
        missing = [i for i in items if i.status == AuditItemStatus.MISSING]
        damaged = [i for i in items if i.status == AuditItemStatus.DAMAGED]
        pending = [i for i in items if i.status is None]

        summary = AuditReportSummary(
            total_items=len(items),
            verified=len(verified),
            missing=len(missing),
            damaged=len(damaged),
            pending=len(pending),
        )
        return AuditReport(
            cycle_id=cycle.id,
            cycle_name=cycle.name,
            status=cycle.status,
            summary=summary,
            discrepancy_count=len(missing) + len(damaged),
            verified_assets=[AuditItemRead.model_validate(i) for i in verified],
            missing_assets=[AuditItemRead.model_validate(i) for i in missing],
            damaged_assets=[AuditItemRead.model_validate(i) for i in damaged],
        )


# Module-level singleton; stateless, so safe to share across requests.
asset_audit_service = AssetAuditService()
