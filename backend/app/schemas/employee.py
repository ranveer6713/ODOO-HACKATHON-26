from pydantic import BaseModel
from typing import Optional
from app.schemas.user import UserResponse


class EmployeeBase(BaseModel):
    employee_code: Optional[str] = None
    department_id: Optional[int] = None
    is_active: Optional[bool] = True


class EmployeeCreate(EmployeeBase):
    user_id: int


class EmployeeUpdate(BaseModel):
    employee_code: Optional[str] = None
    department_id: Optional[int] = None
    is_active: Optional[bool] = None


class EmployeeResponse(EmployeeBase):
    id: int
    user_id: int
    user: Optional[UserResponse] = None

    class Config:
        orm_mode = True
        from_attributes = True
