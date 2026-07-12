from pydantic import BaseModel, EmailStr
from typing import Optional
from app.schemas.role import RoleResponse


class UserBase(BaseModel):
    name: str
    email: EmailStr
    is_active: Optional[bool] = True


class UserCreate(UserBase):
    password: str
    role_id: int


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    role_id: Optional[int] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    id: int
    role_id: int
    role: Optional[RoleResponse] = None

    class Config:
        orm_mode = True
        from_attributes = True
