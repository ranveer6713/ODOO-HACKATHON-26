from pydantic import BaseModel
from typing import Optional, Any, Dict


class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    category_specific_fields: Optional[Dict[str, Any]] = None  # JSON schema template
    is_active: Optional[bool] = True


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category_specific_fields: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class CategoryResponse(CategoryBase):
    id: int

    class Config:
        orm_mode = True
        from_attributes = True
