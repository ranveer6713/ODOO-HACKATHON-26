from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.department import Department
from app.models.employee import Employee
from app.schemas.department import DepartmentCreate, DepartmentUpdate, DepartmentResponse
from app.routers.deps import RoleChecker

router = APIRouter(prefix="/departments", tags=["Departments"])

# Permissions: Admin-only
admin_only = RoleChecker(["Admin"])


@router.get("/", response_model=List[DepartmentResponse])
def list_departments(
    db: Session = Depends(get_db),
    current_user=Depends(admin_only)
):
    departments = db.query(Department).all()
    # Populate parent_name dynamically
    results = []
    for dept in departments:
        parent_name = None
        if dept.parent_department_id:
            parent = db.query(Department).filter(Department.id == dept.parent_department_id).first()
            if parent:
                parent_name = parent.name
        
        results.append(
            DepartmentResponse(
                id=dept.id,
                name=dept.name,
                parent_department_id=dept.parent_department_id,
                department_head_id=dept.department_head_id,
                is_active=dept.is_active,
                parent_name=parent_name
            )
        )
    return results


@router.get("/{id}", response_model=DepartmentResponse)
def get_department(
    id: int,
    db: Session = Depends(get_db),
    current_user=Depends(admin_only)
):
    dept = db.query(Department).filter(Department.id == id).first()
    if not dept:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found"
        )
    
    parent_name = None
    if dept.parent_department_id:
        parent = db.query(Department).filter(Department.id == dept.parent_department_id).first()
        if parent:
            parent_name = parent.name
            
    return DepartmentResponse(
        id=dept.id,
        name=dept.name,
        parent_department_id=dept.parent_department_id,
        department_head_id=dept.department_head_id,
        is_active=dept.is_active,
        parent_name=parent_name
    )


@router.post("/", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
def create_department(
    dept_in: DepartmentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(admin_only)
):
    # Check if duplicate name
    existing = db.query(Department).filter(Department.name == dept_in.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Department with this name already exists"
        )
        
    # Check parent department if provided
    if dept_in.parent_department_id:
        parent = db.query(Department).filter(Department.id == dept_in.parent_department_id).first()
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent department not found"
            )
        if not parent.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Parent department is inactive"
            )

    # Check head employee if provided
    if dept_in.department_head_id:
        head = db.query(Employee).filter(Employee.id == dept_in.department_head_id).first()
        if not head:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Department head employee not found"
            )
        if not head.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Department head employee is inactive"
            )

    dept = Department(
        name=dept_in.name,
        parent_department_id=dept_in.parent_department_id,
        department_head_id=dept_in.department_head_id,
        is_active=dept_in.is_active if dept_in.is_active is not None else True
    )
    db.add(dept)
    db.commit()
    db.refresh(dept)
    
    # Return response
    parent_name = None
    if dept.parent_department_id:
        parent = db.query(Department).filter(Department.id == dept.parent_department_id).first()
        if parent:
            parent_name = parent.name
            
    return DepartmentResponse(
        id=dept.id,
        name=dept.name,
        parent_department_id=dept.parent_department_id,
        department_head_id=dept.department_head_id,
        is_active=dept.is_active,
        parent_name=parent_name
    )


@router.put("/{id}", response_model=DepartmentResponse)
def update_department(
    id: int,
    dept_in: DepartmentUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(admin_only)
):
    dept = db.query(Department).filter(Department.id == id).first()
    if not dept:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")

    if dept_in.name is not None:
        # Check if duplicate name (and not this department)
        existing = db.query(Department).filter(Department.name == dept_in.name, Department.id != id).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Department with this name already exists"
            )
        dept.name = dept_in.name

    if dept_in.parent_department_id is not None:
        if dept_in.parent_department_id == id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A department cannot be its own parent"
            )
        parent = db.query(Department).filter(Department.id == dept_in.parent_department_id).first()
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent department not found"
            )
        if not parent.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Parent department is inactive"
            )
        dept.parent_department_id = dept_in.parent_department_id

    if dept_in.department_head_id is not None:
        head = db.query(Employee).filter(Employee.id == dept_in.department_head_id).first()
        if not head:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Department head employee not found"
            )
        if not head.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Department head employee is inactive"
            )
        dept.department_head_id = dept_in.department_head_id

    if dept_in.is_active is not None:
        dept.is_active = dept_in.is_active

    db.commit()
    db.refresh(dept)
    
    parent_name = None
    if dept.parent_department_id:
        parent = db.query(Department).filter(Department.id == dept.parent_department_id).first()
        if parent:
            parent_name = parent.name
            
    return DepartmentResponse(
        id=dept.id,
        name=dept.name,
        parent_department_id=dept.parent_department_id,
        department_head_id=dept.department_head_id,
        is_active=dept.is_active,
        parent_name=parent_name
    )


@router.delete("/{id}", response_model=DepartmentResponse)
def deactivate_department(
    id: int,
    db: Session = Depends(get_db),
    current_user=Depends(admin_only)
):
    dept = db.query(Department).filter(Department.id == id).first()
    if not dept:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")

    dept.is_active = False
    db.commit()
    db.refresh(dept)
    
    parent_name = None
    if dept.parent_department_id:
        parent = db.query(Department).filter(Department.id == dept.parent_department_id).first()
        if parent:
            parent_name = parent.name
            
    return DepartmentResponse(
        id=dept.id,
        name=dept.name,
        parent_department_id=dept.parent_department_id,
        department_head_id=dept.department_head_id,
        is_active=dept.is_active,
        parent_name=parent_name
    )
