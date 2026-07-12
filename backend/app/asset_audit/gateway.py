"""AssetGateway — anti-corruption layer for the shared ``assets`` table.

The Asset Audit module never defines or imports an ``Asset`` ORM model. Doing so
would couple us to another team's schema and pollute our metadata. Instead every
asset read/write goes through this narrow gateway using SQLAlchemy Core against
the documented contract only.

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
from typing import List, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.asset_audit.exceptions import NotFoundError


class AssetStatus(str, enum.Enum):
    """Lifecycle states of an asset (canonical column lives in ``assets``)."""

    AVAILABLE = "available"
    BOOKED = "booked"
    UNDER_MAINTENANCE = "under_maintenance"
    RETIRED = "retired"
    DISPOSED = "disposed"
    LOST = "lost"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class AssetInfo:
    id: str
    name: str
    status: AssetStatus


class AssetGateway:
    """Read/write access to the shared ``assets`` table via SQLAlchemy Core.

    The Asset Audit workflow only ever *reads* assets and, on close, transitions
    confirmed-missing assets to :attr:`AssetStatus.LOST` via :meth:`mark_lost`.
    """

    def _row_to_info(self, row) -> AssetInfo:
        raw_status = row["status"]
        try:
            status = AssetStatus(raw_status)
        except ValueError:
            # Unknown status coming from the Asset module: treat conservatively
            # as retired rather than guessing it is serviceable.
            status = AssetStatus.RETIRED
        return AssetInfo(id=str(row["id"]), name=row["name"], status=status)

    def get_asset(self, db: Session, asset_id: str) -> Optional[AssetInfo]:
        """Fetch one asset by id, or ``None`` if it does not exist."""
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
        return self.get_asset(db, asset_id) is not None

    def require(self, db: Session, asset_id: str) -> AssetInfo:
        info = self.get_asset(db, asset_id)
        if info is None:
            raise NotFoundError(f"Asset '{asset_id}' does not exist")
        return info

    def list_assets(
        self, db: Session, *, status: Optional[AssetStatus] = None
    ) -> List[AssetInfo]:
        """List assets, optionally filtered by status (read-only)."""
        if status is not None:
            rows = db.execute(
                text(
                    "SELECT id, name, status FROM assets "
                    "WHERE status = :status ORDER BY id"
                ),
                {"status": status.value},
            ).mappings().all()
        else:
            rows = db.execute(
                text("SELECT id, name, status FROM assets ORDER BY id")
            ).mappings().all()
        return [self._row_to_info(row) for row in rows]

    def set_status(self, db: Session, asset_id: str, status: AssetStatus) -> None:
        """Transition an asset's status. Asset Audit mutates assets only here."""
        result = db.execute(
            text("UPDATE assets SET status = :status WHERE id = :id"),
            {"status": status.value, "id": asset_id},
        )
        if result.rowcount == 0:
            raise NotFoundError(f"Asset '{asset_id}' does not exist")

    def mark_lost(self, db: Session, asset_id: str) -> None:
        """Flag a confirmed-missing asset as lost (audit close outcome)."""
        self.set_status(db, asset_id, AssetStatus.LOST)


# Module-level singleton; stateless, so safe to share across requests.
asset_gateway = AssetGateway()
