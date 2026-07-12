"""ActivityLogService — writes workflow activity entries.

The Workflow module *creates* log entries for its own domain events but does NOT
own the Activity Log infrastructure (table schema, retention, viewer). Entries
are written against the shared ``activity_logs`` contract via Core, so ownership
of the table stays with the shared foundation.
"""
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session


class ActivityLogService:
    def __init__(self, db: Session):
        self.db = db

    def log(
        self,
        *,
        actor_id: str,
        action: str,
        entity_type: str,
        entity_id: str,
        detail: Optional[str] = None,
    ) -> None:
        self.db.execute(
            text(
                "INSERT INTO activity_logs "
                "(actor_id, action, entity_type, entity_id, detail) "
                "VALUES (:actor_id, :action, :entity_type, :entity_id, :detail)"
            ),
            {
                "actor_id": actor_id,
                "action": action,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "detail": detail,
            },
        )
