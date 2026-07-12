from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime


class AssetHistoryResponse(BaseModel):
    id: int
    asset_id: int
    action: str
    action_by_id: int
    action_date: datetime
    notes: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

    class Config:
        orm_mode = True
        from_attributes = True
