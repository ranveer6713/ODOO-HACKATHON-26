"""AssetGateway — anti-corruption layer for the shared ``assets`` table.

The Maintenance module never defines or imports an ``Asset`` ORM model. Doing so
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
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.maintenance.exceptions import NotFoundError, ValidationError


class AssetStatus(str, enum.Enum):
    """Lifecycle states of an asset (canonical column lives in ``assets``)."""

    AVAILABLE = "available"
    BOOKED = "booked"
    UNDER_MAINTENANCE = "under_maintenance"
    RETIRED = "retired"
    DISPOSED = "disposed"
    LOST = "lost"
    CANCELLED = "cancelled"


# Asset states on which a maintenance request may not be raised. A disposed asset
# has left the estate permanently and can never re-enter the maintenance workflow.
MAINTENANCE_BLOCKED_ASSET_STATES = frozenset({AssetStatus.DISPOSED})


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
            # as retired rather than guessing it is serviceable.
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
        """Transition an asset's status. Maintenance mutates assets only here."""
        result = db.execute(
            text("UPDATE assets SET status = :status WHERE id = :id"),
            {"status": status.value, "id": asset_id},
        )
        if result.rowcount == 0:
            raise NotFoundError(f"Asset '{asset_id}' does not exist")

    def assert_maintainable(self, db: Session, asset_id: str) -> AssetInfo:
        """Guarantee an asset can enter the maintenance workflow.

        Enforces the rule *disposed assets cannot enter maintenance*.
        """
        info = self.require(db, asset_id)
        if info.status in MAINTENANCE_BLOCKED_ASSET_STATES:
            raise ValidationError(
                f"Cannot raise a maintenance request for asset '{info.name}' "
                f"because it is '{info.status.value}'"
            )
        return info


# Module-level singleton; stateless, so safe to share across requests.
asset_gateway = AssetGateway()
