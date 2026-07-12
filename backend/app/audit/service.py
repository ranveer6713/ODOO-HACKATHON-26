"""Audit business logic — the append-only activity trail.

Two responsibilities:

    * :meth:`record` — the shared logging port. Every workflow action across the
      backend (Maintenance, Booking, and Audit's own review actions) calls it.
      It only ``add`` + ``flush`` so the log entry commits atomically with the
      workflow change that produced it (the caller owns the commit).
    * the review lifecycle (:meth:`flag` / :meth:`acknowledge`) — router-facing
      manager actions that own their commit, notify the actor through the shared
      :class:`NotificationService`, and are themselves recorded to the trail
      (every workflow action creates an activity-log entry, including these).

The notifier is injected (defaulting to the shared singleton) so the module has
no global mutable state and stays unit-testable. Stateless; the DB session is
passed in per call.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional, Tuple, Union

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.audit import validators
from app.audit.deps import Principal, Role
from app.audit.exceptions import NotFoundError, PermissionDeniedError, ValidationError
from app.audit.models import ActivityLog, AuditSeverity
from app.notifications.models import NotificationType
from app.notifications.service import NotificationService, notification_service

_MANAGER_ROLES = (Role.ASSET_MANAGER, Role.ADMIN)

_SORTABLE_FIELDS = {
    "created_at": ActivityLog.created_at,
    "severity": ActivityLog.severity,
    "action": ActivityLog.action,
    "id": ActivityLog.id,
}

# Entity type used when the audit module records actions against its own trail.
ENTITY_ACTIVITY_LOG = "activity_log"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _coerce_severity(value: Union[str, AuditSeverity]) -> AuditSeverity:
    if isinstance(value, AuditSeverity):
        return value
    try:
        return AuditSeverity(value)
    except ValueError as exc:
        raise ValidationError(f"Unknown severity '{value}'") from exc


class AuditService:
    """Stateless orchestrator; the DB session is passed in per call."""

    def __init__(self, *, notifier: Optional[NotificationService] = None) -> None:
        # Dependency injection with a sensible default; no global mutable state.
        self._notifier = notifier or notification_service

    # ------------------------------------------------------------------ access
    def _is_manager(self, principal: Principal) -> bool:
        return principal.role in _MANAGER_ROLES

    def _require(self, db: Session, entry_id: int) -> ActivityLog:
        entry = db.get(ActivityLog, entry_id)
        if entry is None:
            raise NotFoundError(f"Activity log entry {entry_id} does not exist")
        return entry

    # ----------------------------------------------------------- logging port
    def record(
        self,
        db: Session,
        *,
        actor_id: str,
        action: str,
        entity_type: str,
        entity_id: str,
        description: Optional[str] = None,
        severity: Union[str, AuditSeverity] = AuditSeverity.INFO,
    ) -> ActivityLog:
        """Append one entry to the audit trail.

        Called by sibling workflow services *inside their transaction*: this
        method never commits, so the log entry and the workflow mutation that
        triggered it are persisted together (or rolled back together).
        """
        validators.validate_record_fields(actor_id, action, entity_type, entity_id)

        entry = ActivityLog(
            actor_id=actor_id,
            action=action.strip(),
            entity_type=entity_type.strip(),
            entity_id=str(entity_id).strip(),
            description=description,
            severity=_coerce_severity(severity),
        )
        db.add(entry)
        db.flush()
        return entry

    # ------------------------------------------------------------------- reads
    def get(self, db: Session, principal: Principal, entry_id: int) -> ActivityLog:
        entry = self._require(db, entry_id)
        if not self._is_manager(principal) and entry.actor_id != principal.id:
            raise PermissionDeniedError(
                "You are not allowed to view this activity log entry"
            )
        return entry

    def list(
        self,
        db: Session,
        principal: Principal,
        *,
        actor_id: Optional[str] = None,
        action: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        severity: Optional[Union[str, AuditSeverity]] = None,
        flagged: Optional[bool] = None,
        search: Optional[str] = None,
        sort_by: str = "created_at",
        order: str = "desc",
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[ActivityLog], int]:
        conditions = []
        # Non-managers only ever see their own actions.
        if not self._is_manager(principal):
            conditions.append(ActivityLog.actor_id == principal.id)
        elif actor_id is not None:
            conditions.append(ActivityLog.actor_id == actor_id)

        if action is not None:
            conditions.append(ActivityLog.action == action)
        if entity_type is not None:
            conditions.append(ActivityLog.entity_type == entity_type)
        if entity_id is not None:
            conditions.append(ActivityLog.entity_id == str(entity_id))
        if severity is not None:
            conditions.append(ActivityLog.severity == _coerce_severity(severity))
        if flagged is not None:
            conditions.append(ActivityLog.flagged.is_(flagged))
        if search:
            term = f"%{search.strip()}%"
            conditions.append(
                or_(
                    ActivityLog.description.ilike(term),
                    ActivityLog.action.ilike(term),
                )
            )

        where = and_(*conditions) if conditions else None

        count_query = select(func.count()).select_from(ActivityLog)
        if where is not None:
            count_query = count_query.where(where)
        total = db.execute(count_query).scalar_one()

        column = _SORTABLE_FIELDS.get(sort_by, ActivityLog.created_at)
        column = column.desc() if order.lower() == "desc" else column.asc()

        query = select(ActivityLog)
        if where is not None:
            query = query.where(where)
        query = (
            query.order_by(column, ActivityLog.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        rows = list(db.execute(query).scalars().all())
        return rows, total

    # ------------------------------------------------------- review lifecycle
    def flag(
        self, db: Session, principal: Principal, entry_id: int, reason: str
    ) -> ActivityLog:
        """Flag an entry for review (managers/admins only) and alert the actor."""
        if not self._is_manager(principal):
            raise PermissionDeniedError(
                "Only asset managers can flag activity log entries"
            )
        entry = self._require(db, entry_id)
        validators.validate_can_flag(entry)

        entry.flagged = True
        entry.flagged_by = principal.id
        entry.flag_reason = reason
        entry.flagged_at = _utcnow()

        # Alert the actor whose action was flagged (shared notification port).
        self._notifier.notify(
            db,
            recipient_id=entry.actor_id,
            type=NotificationType.AUDIT,
            title="An activity of yours was flagged for review",
            message=(
                f"Your '{entry.action}' action on "
                f"{entry.entity_type} {entry.entity_id} was flagged: {reason}"
            ),
            entity_type=ENTITY_ACTIVITY_LOG,
            entity_id=str(entry.id),
        )
        # Flagging is itself a workflow action -> record it to the trail.
        self.record(
            db,
            actor_id=principal.id,
            action="flagged",
            entity_type=ENTITY_ACTIVITY_LOG,
            entity_id=str(entry.id),
            description=f"Flagged for review: {reason}",
            severity=AuditSeverity.WARNING,
        )

        db.commit()
        db.refresh(entry)
        return entry

    def acknowledge(
        self, db: Session, principal: Principal, entry_id: int
    ) -> ActivityLog:
        """Acknowledge a flagged entry (the actor themselves, or an admin)."""
        entry = self._require(db, entry_id)
        if not principal.is_admin and entry.actor_id != principal.id:
            raise PermissionDeniedError(
                "Only the actor or an admin can acknowledge this entry"
            )
        validators.validate_can_acknowledge(entry)

        entry.acknowledged = True
        entry.acknowledged_by = principal.id
        entry.acknowledged_at = _utcnow()

        self.record(
            db,
            actor_id=principal.id,
            action="acknowledged",
            entity_type=ENTITY_ACTIVITY_LOG,
            entity_id=str(entry.id),
            description="Flag acknowledged",
            severity=AuditSeverity.INFO,
        )

        db.commit()
        db.refresh(entry)
        return entry


# Module-level singleton; stateless, so safe to share across requests.
audit_service = AuditService()
