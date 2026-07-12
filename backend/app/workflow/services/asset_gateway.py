"""AssetGateway — anti-corruption layer for the shared ``assets`` table.

The Workflow module never defines or imports an Asset ORM model. Every asset
read/write goes through this gateway using SQLAlchemy Core against the documented
contract only:  ``assets(id, name, status, is_bookable)``.  This keeps the
Asset model fully owned by another developer while giving Booking / Maintenance a
stable interface.
"""
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session


class AssetGateway:
    def __init__(self, db: Session):
        self.db = db

    def get(self, asset_id: str) -> Optional[dict]:
        row = (
            self.db.execute(
                text("SELECT id, name, status, is_bookable FROM assets WHERE id = :id"),
                {"id": asset_id},
            )
            .mappings()
            .first()
        )
        return dict(row) if row else None

    def exists(self, asset_id: str) -> bool:
        return self.get(asset_id) is not None

    def is_bookable(self, asset_id: str) -> bool:
        asset = self.get(asset_id)
        return bool(asset and asset["is_bookable"])

    def set_status(self, asset_id: str, status: str) -> None:
        """Maintenance transitions an asset's status through this method only."""
        self.db.execute(
            text("UPDATE assets SET status = :status WHERE id = :id"),
            {"status": status, "id": asset_id},
        )
