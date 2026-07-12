from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.employee import Employee
from app.models.user import User
from app.models.role import Role
from app.schemas.employee import EmployeeCreate, EmployeeUpdate, EmployeeResponse
from app.schemas.user import UserCreate
from app.core.security import get_password_hash
from app.routers.deps import RoleChecker

router = APIRouter(prefix="/employees", tags=["Employees"])

# Permissions
admin_or_manager = RoleChecker(["Admin", "Asset Manager"])


@router.get("/", response_model=List[EmployeeResponse])
def list_employees(db: Session = Depends(get_db)):
    return db.query(Employee).all()


@router.post("/", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
def create_employee(
    emp_in: EmployeeCreate,
    db: Session = Depends(get_db),
    current_user=Depends(admin_or_manager)
):
    # Verify user exists
    user = db.query(User).filter(User.id == emp_in.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Associated User not found"
        )
        
    # Check if employee record already exists for user
    existing = db.query(Employee).filter(Employee.user_id == emp_in.user_id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Employee record already exists for this user"
        )

    # Check code uniqueness
    if emp_in.employee_code:
        existing_code = db.query(Employee).filter(Employee.employee_code == emp_in.employee_code).first()
        if existing_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Employee code already in use"
            )

    emp = Employee(
        user_id=emp_in.user_id,
        employee_code=emp_in.employee_code,
        department_id=emp_in.department_id,
        is_active=emp_in.is_active
    )
    db.add(emp)
    db.commit()
    db.refresh(emp)
    return emp


@router.put("/{id}", response_model=EmployeeResponse)
def update_employee(
    id: int,
    emp_in: EmployeeUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(admin_or_manager)
):
    emp = db.query(Employee).filter(Employee.id == id).first()
    if not emp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

    if emp_in.employee_code is not None:
        # Check uniqueness
        existing_code = db.query(Employee).filter(
            Employee.employee_code == emp_in.employee_code,
            Employee.id != id
        ).first()
        if existing_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Employee code already in use"
            )
        emp.employee_code = emp_in.employee_code

    if emp_in.department_id is not None:
        emp.department_id = emp_in.department_id

    if emp_in.is_active is not None:
        emp.is_active = emp_in.is_active
        # Optionally deactivate the associated User account too
        emp.user.is_active = emp_in.is_active

    db.commit()
    db.refresh(emp)
    return emp


@router.delete("/{id}", response_model=EmployeeResponse)
def deactivate_employee(
    id: int,
    db: Session = Depends(get_db),
    current_user=Depends(admin_or_manager)
):
    emp = db.query(Employee).filter(Employee.id == id).first()
    if not emp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

    emp.is_active = False
    emp.user.is_active = False
    db.commit()
    db.refresh(emp)
    return emp


@router.post("/{id}/promote-manager", response_model=EmployeeResponse)
def promote_to_manager(
    id: int,
    db: Session = Depends(get_db),
    current_user=Depends(RoleChecker(["Admin"]))
):
    emp = db.query(Employee).filter(Employee.id == id).first()
    if not emp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

    # Find the "Asset Manager" role
    role = db.query(Role).filter(Role.name == "Asset Manager").first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Asset Manager role not configured"
        )

    emp.user.role_id = role.id
    db.commit()
    db.refresh(emp)
    return emp


@router.post("/{id}/promote-head", response_model=EmployeeResponse)
def promote_to_head(
    id: int,
    db: Session = Depends(get_db),
    current_user=Depends(RoleChecker(["Admin", "Asset Manager"]))
):
    emp = db.query(Employee).filter(Employee.id == id).first()
    if not emp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

    # Find the "Department Head" role
    role = db.query(Role).filter(Role.name == "Department Head").first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Department Head role not configured"
        )

    emp.user.role_id = role.id
    db.commit()
    db.refresh(emp)
    return emp
