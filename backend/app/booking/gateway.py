"""AssetGateway — anti-corruption layer for the shared ``assets`` table.

The Booking module never defines or imports an ``Asset`` ORM model. Doing so
would couple us to another team's schema and pollute our metadata. Instead every
asset read/write goes through this narrow gateway using SQLAlchemy Core against
the documented contract only. It exposes booking-specific asset semantics
(``assert_bookable``, ``mark_booked``, ``mark_available``) — the module's sole
seam onto the asset estate.

Expected ``assets`` table contract (owned by the Asset module):
    - ``id``          TEXT / VARCHAR  -- string primary key (string-FK contract)
    - ``name``        TEXT
    - ``status``      TEXT            -- one of :class:`AssetStatus` values

Only these columns are read; ``status`` is the only column ever written. Any
additional columns owned by the Asset module are left untouched.
"""
from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.booking.exceptions import NotFoundError, ValidationError


class AssetStatus(str, enum.Enum):
    """Lifecycle states of an asset (canonical column lives in ``assets``)."""

    AVAILABLE = "available"
    BOOKED = "booked"
    UNDER_MAINTENANCE = "under_maintenance"
    RETIRED = "retired"
    DISPOSED = "disposed"
    LOST = "lost"
    CANCELLED = "cancelled"


# Asset states on which a booking may not be raised. An asset that is under
# maintenance, retired, disposed or lost is not available to reserve; a currently
# ``BOOKED`` asset can still take future (non-overlapping) reservations, so it is
# deliberately *not* blocked here — overlap is enforced against the bookings table.
BOOKING_BLOCKED_ASSET_STATES = frozenset(
    {
        AssetStatus.UNDER_MAINTENANCE,
        AssetStatus.RETIRED,
        AssetStatus.DISPOSED,
        AssetStatus.LOST,
    }
)


@dataclass(frozen=True)
class AssetInfo:
    id: str
    name: str
    status: AssetStatus


class AssetGateway:
    """Read/write access to the shared ``assets`` table via SQLAlchemy Core."""

    def _row_to_info(self, row) -> AssetInfo:
        raw_status = row["status"]
        try:
            status = AssetStatus(raw_status)
        except ValueError:
            # Unknown status coming from the Asset module: treat conservatively
            # as retired rather than guessing it is bookable.
            status = AssetStatus.RETIRED
        return AssetInfo(id=str(row["id"]), name=row["name"], status=status)

    def get(self, db: Session, asset_id: str) -> Optional[AssetInfo]:
        row = (
            db.execute(
                text("SELECT id, name, status FROM assets WHERE id = :id"),
                {"id": asset_id},
            )
            .mappings()
            .first()
        )
        return self._row_to_info(row) if row is not None else None

    def exists(self, db: Session, asset_id: str) -> bool:
        return self.get(db, asset_id) is not None

    def require(self, db: Session, asset_id: str) -> AssetInfo:
        info = self.get(db, asset_id)
        if info is None:
            raise NotFoundError(f"Asset '{asset_id}' does not exist")
        return info

    def set_status(self, db: Session, asset_id: str, status: AssetStatus) -> None:
        """Transition an asset's status. Booking mutates assets only here."""
        result = db.execute(
            text("UPDATE assets SET status = :status WHERE id = :id"),
            {"status": status.value, "id": asset_id},
        )
        if result.rowcount == 0:
            raise NotFoundError(f"Asset '{asset_id}' does not exist")

    def mark_booked(self, db: Session, asset_id: str) -> None:
        self.set_status(db, asset_id, AssetStatus.BOOKED)

    def mark_available(self, db: Session, asset_id: str) -> None:
        self.set_status(db, asset_id, AssetStatus.AVAILABLE)

    def assert_bookable(self, db: Session, asset_id: str) -> AssetInfo:
        """Guarantee an asset can be reserved.

        Enforces the rule *unavailable assets (under maintenance / retired /
        disposed / lost) cannot be booked*.
        """
        info = self.require(db, asset_id)
        if info.status in BOOKING_BLOCKED_ASSET_STATES:
            raise ValidationError(
                f"Cannot book asset '{info.name}' because it is "
                f"'{info.status.value}'"
            )
        return info


# Module-level singleton; stateless, so safe to share across requests.
asset_gateway = AssetGateway()
