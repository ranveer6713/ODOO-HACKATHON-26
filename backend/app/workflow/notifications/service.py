"""NotificationService — reusable business-event notification generation.

There is no application-level notification center here. Workflow services call
``NotificationService`` to emit notifications for domain events (booking
reminder, maintenance status change, audit discrepancy, ...). Recipients are
referenced by ``users.id`` (string FK); no User model is defined.
"""
from typing import Optional

from sqlalchemy.orm import Session


class NotificationService:
    def __init__(self, db: Session):
        self.db = db

    def notify(
        self,
        *,
        recipient_id: str,
        event: str,
        payload: Optional[dict] = None,
    ) -> None:
        """Generate a notification for a business event."""
        raise NotImplementedError
