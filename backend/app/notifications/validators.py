"""Notification business-rule guards.

These framework-agnostic guards are the single source of truth for notification
access and content rules. They never touch the database, which keeps them trivial
to unit-test in isolation. The service layer calls them before mutating state.
"""
from __future__ import annotations

from app.notifications.deps import Principal
from app.notifications.exceptions import PermissionDeniedError, ValidationError
from app.notifications.models import Notification


def validate_recipient_id(recipient_id: str) -> str:
    """Rule: a notification must be addressed to a concrete recipient."""
    recipient_id = (recipient_id or "").strip()
    if not recipient_id:
        raise ValidationError("A notification requires a recipient_id")
    return recipient_id


def validate_content(title: str, message: str) -> None:
    """Rule: a notification must carry a non-blank title and message."""
    if not (title or "").strip():
        raise ValidationError("A notification requires a non-blank title")
    if not (message or "").strip():
        raise ValidationError("A notification requires a non-blank message")


def validate_can_access(notification: Notification, principal: Principal) -> None:
    """Rule: only the recipient (or an admin) may read/mutate a notification."""
    if principal.is_admin:
        return
    if notification.recipient_id != principal.id:
        raise PermissionDeniedError(
            "You are not allowed to access this notification"
        )
