"""Dashboard domain vocabulary — classification enums and mappings.

The Dashboard is a pure read/aggregation layer and therefore owns **no** ORM
tables; there is no ``__tablename__`` in this module. What it *does* own is the
vocabulary it uses to fold raw sibling data into presentation buckets — the KPI
asset buckets and the catalogue of quick actions. Keeping that vocabulary here
(rather than sprinkled through the service) makes the mapping auditable and lets
schemas/service share one source of truth.
"""
from __future__ import annotations

import enum
from typing import Dict


class AssetKpiBucket(str, enum.Enum):
    """The KPI buckets the dashboard reports asset counts in.

    The canonical ``assets.status`` column (owned by the Asset module) is folded
    into these buckets. ``booked`` — the status Booking assigns to an asset while
    it is checked out — is surfaced as :attr:`ALLOCATED` (the asset is in a
    user's hands); a distinct ``reserved`` status, if the Asset module exposes
    one, maps to :attr:`RESERVED`. Any status we do not recognise is counted
    under :attr:`OTHER` so totals always reconcile.
    """

    AVAILABLE = "available"
    ALLOCATED = "allocated"
    RESERVED = "reserved"
    UNDER_MAINTENANCE = "under_maintenance"
    LOST = "lost"
    DISPOSED = "disposed"
    RETIRED = "retired"
    OTHER = "other"


# Canonical ``assets.status`` string -> KPI bucket. Kept lowercase; the gateway
# lower-cases raw values before lookup so casing from the Asset module is
# irrelevant. Unmapped statuses fall through to :attr:`AssetKpiBucket.OTHER`.
ASSET_STATUS_TO_BUCKET: Dict[str, AssetKpiBucket] = {
    "available": AssetKpiBucket.AVAILABLE,
    "allocated": AssetKpiBucket.ALLOCATED,
    "booked": AssetKpiBucket.ALLOCATED,
    "checked_out": AssetKpiBucket.ALLOCATED,
    "reserved": AssetKpiBucket.RESERVED,
    "under_maintenance": AssetKpiBucket.UNDER_MAINTENANCE,
    "maintenance": AssetKpiBucket.UNDER_MAINTENANCE,
    "lost": AssetKpiBucket.LOST,
    "disposed": AssetKpiBucket.DISPOSED,
    "retired": AssetKpiBucket.RETIRED,
}


def bucket_for_status(raw_status: str) -> AssetKpiBucket:
    """Fold a raw ``assets.status`` value into its KPI bucket."""
    if raw_status is None:
        return AssetKpiBucket.OTHER
    return ASSET_STATUS_TO_BUCKET.get(
        str(raw_status).strip().lower(), AssetKpiBucket.OTHER
    )


class QuickActionKey(str, enum.Enum):
    """Stable identifiers for the quick-action shortcuts the dashboard offers.

    The dashboard only *describes* these actions (returns DTOs pointing at the
    owning module's endpoint); it never performs them. The owning module remains
    the single source of truth for the behaviour and its authorization.
    """

    NEW_BOOKING = "new_booking"
    RAISE_MAINTENANCE = "raise_maintenance"
    START_AUDIT_CYCLE = "start_audit_cycle"
    REVIEW_PENDING_BOOKINGS = "review_pending_bookings"
    REVIEW_PENDING_MAINTENANCE = "review_pending_maintenance"
    VIEW_NOTIFICATIONS = "view_notifications"
