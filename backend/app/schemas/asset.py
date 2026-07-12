from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import date
from app.schemas.category import CategoryResponse


class AssetBase(BaseModel):
    name: str
    description: Optional[str] = None
    category_id: int
    image_url: Optional[str] = None
    document_urls: Optional[List[str]] = None
    is_bookable: Optional[bool] = False
    status: Optional[str] = "Available"  # Available, Allocated, Reserved, Under Maintenance, Lost, Retired, Disposed
    serial_number: Optional[str] = None
    purchase_date: Optional[date] = None
    purchase_cost: Optional[float] = None
    warranty_expiry: Optional[date] = None
    category_specific_data: Optional[Dict[str, Any]] = None


class AssetCreate(AssetBase):
    asset_tag: Optional[str] = None  # Can be auto-generated if not provided


class AssetUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[int] = None
    image_url: Optional[str] = None
    document_urls: Optional[List[str]] = None
    is_bookable: Optional[bool] = None
    status: Optional[str] = None
    serial_number: Optional[str] = None
    purchase_date: Optional[date] = None
    purchase_cost: Optional[float] = None
    warranty_expiry: Optional[date] = None
    category_specific_data: Optional[Dict[str, Any]] = None


class AssetResponse(AssetBase):
    id: int
    asset_tag: str
    category: Optional[CategoryResponse] = None

    class Config:
        orm_mode = True
        from_attributes = True
