from pydantic import BaseModel
from typing import Optional, List


class DepartmentBase(BaseModel):
    name: str
    parent_department_id: Optional[int] = None
    department_head_id: Optional[int] = None
    is_active: Optional[bool] = True


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    parent_department_id: Optional[int] = None
    department_head_id: Optional[int] = None
    is_active: Optional[bool] = None


class DepartmentResponse(DepartmentBase):
    id: int
    # To avoid recursion, let's include basic parent details
    parent_name: Optional[str] = None

    class Config:
        orm_mode = True
        from_attributes = True
