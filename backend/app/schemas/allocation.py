from pydantic import BaseModel, validator
from typing import Optional
from datetime import datetime
from app.schemas.employee import EmployeeResponse
from app.schemas.department import DepartmentResponse


class AllocationBase(BaseModel):
    asset_id: int
    allocated_to_type: str  # "employee" or "department"
    employee_id: Optional[int] = None
    department_id: Optional[int] = None
    expected_return_date: datetime
    condition_on_allocation: Optional[str] = None


class AllocationCreate(AllocationBase):
    @validator("employee_id")
    def validate_employee_id(cls, v, values):
        if values.get("allocated_to_type") == "employee" and not v:
            raise ValueError("employee_id is required when allocated_to_type is 'employee'")
        return v

    @validator("department_id")
    def validate_department_id(cls, v, values):
        if values.get("allocated_to_type") == "department" and not v:
            raise ValueError("department_id is required when allocated_to_type is 'department'")
        return v


class AllocationReturn(BaseModel):
    condition_on_return: Optional[str] = None


class AllocationResponse(AllocationBase):
    id: int
    allocated_by_id: int
    allocated_at: datetime
    returned_at: Optional[datetime] = None
    condition_on_return: Optional[str] = None
    status: str  # "active", "returned", "overdue"

    class Config:
        orm_mode = True
        from_attributes = True
