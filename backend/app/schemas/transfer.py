from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class TransferRequest(BaseModel):
    asset_id: int
    to_employee_id: int
    notes: Optional[str] = None


class TransferAction(BaseModel):
    status: str  # "approved" or "rejected"
    notes: Optional[str] = None


class TransferResponse(BaseModel):
    id: int
    asset_id: int
    from_employee_id: int
    to_employee_id: int
    requested_by_id: int
    approved_by_id: Optional[int] = None
    request_date: datetime
    action_date: Optional[datetime] = None
    status: str
    notes: Optional[str] = None

    class Config:
        orm_mode = True
        from_attributes = True
