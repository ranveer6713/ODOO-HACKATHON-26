from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List

from app.database import get_db
from app.models.allocation import Allocation
from app.models.asset import Asset
from app.models.employee import Employee
from app.models.department import Department
from app.models.asset_history import AssetHistory
from app.schemas.allocation import AllocationCreate, AllocationReturn, AllocationResponse
from app.routers.deps import get_current_user, RoleChecker

router = APIRouter(prefix="/allocations", tags=["Allocations"])

# Permissions
admin_or_manager = RoleChecker(["Admin", "Asset Manager"])


@router.get("/", response_model=List[AllocationResponse])
def list_allocations(
    status: str = Query("active", description="Filter by status: 'active', 'returned', 'overdue', 'all'"),
    db: Session = Depends(get_db)
):
    query = db.query(Allocation)
    now = datetime.utcnow()
    
    if status == "active":
        query = query.filter(Allocation.status == "active", Allocation.returned_at == None)
    elif status == "returned":
        query = query.filter(Allocation.returned_at != None)
    elif status == "overdue":
        query = query.filter(
            Allocation.status == "active",
            Allocation.expected_return_date < now,
            Allocation.returned_at == None
        )
    
    return query.all()


@router.get("/overdue", response_model=List[AllocationResponse])
def get_overdue_allocations(db: Session = Depends(get_db)):
    now = datetime.utcnow()
    # Also update their status in the database to overdue automatically if they are past date
    overdue_list = db.query(Allocation).filter(
        Allocation.status == "active",
        Allocation.expected_return_date < now,
        Allocation.returned_at == None
    ).all()
    
    for alloc in overdue_list:
        alloc.status = "overdue"
    if overdue_list:
        db.commit()
        
    return overdue_list


@router.post("/", response_model=AllocationResponse, status_code=status.HTTP_201_CREATED)
def allocate_asset(
    alloc_in: AllocationCreate,
    db: Session = Depends(get_db),
    current_user=Depends(admin_or_manager)
):
    # Fetch Asset
    asset = db.query(Asset).filter(Asset.id == alloc_in.asset_id).first()
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")

    # Conflict Detection: Check if asset is available
    if asset.status != "Available":
        # Find who holds it currently
        active_alloc = db.query(Allocation).filter(
            Allocation.asset_id == asset.id,
            Allocation.returned_at == None
        ).first()
        
        holder_msg = "Unknown holder"
        if active_alloc:
            if active_alloc.allocated_to_type == "employee" and active_alloc.employee:
                holder_msg = f"Employee {active_alloc.employee.user.name} ({active_alloc.employee.employee_code})"
            elif active_alloc.allocated_to_type == "department" and active_alloc.department:
                holder_msg = f"Department {active_alloc.department.name}"
                
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Asset is currently {asset.status}. Held by: {holder_msg}. You can trigger a Transfer Request instead."
        )

    # Validate target entity exists
    if alloc_in.allocated_to_type == "employee":
        target = db.query(Employee).filter(Employee.id == alloc_in.employee_id).first()
        if not target:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
        if not target.is_active:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Employee is inactive")
    elif alloc_in.allocated_to_type == "department":
        target = db.query(Department).filter(Department.id == alloc_in.department_id).first()
        if not target:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")
        if not target.is_active:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Department is inactive")
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid allocated_to_type")

    # Save allocation
    allocation = Allocation(
        asset_id=alloc_in.asset_id,
        allocated_to_type=alloc_in.allocated_to_type,
        employee_id=alloc_in.employee_id,
        department_id=alloc_in.department_id,
        allocated_by_id=current_user.id,
        allocated_at=datetime.utcnow(),
        expected_return_date=alloc_in.expected_return_date,
        condition_on_allocation=alloc_in.condition_on_allocation,
        status="active"
    )
    db.add(allocation)
    
    # Update Asset Status to "Allocated"
    asset.status = "Allocated"
    db.commit()
    db.refresh(allocation)

    # Log History
    history = AssetHistory(
        asset_id=asset.id,
        action="allocation",
        action_by_id=current_user.id,
        action_date=datetime.utcnow(),
        notes=f"Allocated to {alloc_in.allocated_to_type} (ID: {alloc_in.employee_id or alloc_in.department_id})"
    )
    db.add(history)
    db.commit()

    return allocation


@router.post("/{id}/return", response_model=AllocationResponse)
def return_asset(
    id: int,
    return_in: AllocationReturn,
    db: Session = Depends(get_db),
    current_user=Depends(admin_or_manager)
):
    allocation = db.query(Allocation).filter(Allocation.id == id).first()
    if not allocation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Allocation not found")
    
    if allocation.returned_at is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Asset already returned")

    # Update Allocation details
    allocation.returned_at = datetime.utcnow()
    allocation.condition_on_return = return_in.condition_on_return
    allocation.status = "returned"
    
    # Update Asset Status back to "Available"
    asset = allocation.asset
    asset.status = "Available"
    db.commit()
    db.refresh(allocation)

    # Log History
    history = AssetHistory(
        asset_id=asset.id,
        action="return",
        action_by_id=current_user.id,
        action_date=datetime.utcnow(),
        notes=f"Returned with condition notes: {return_in.condition_on_return or 'None'}"
    )
    db.add(history)
    db.commit()

    return allocation


@router.get("/asset/{asset_id}", response_model=AllocationResponse)
def get_active_allocation_by_asset(asset_id: int, db: Session = Depends(get_db)):
    allocation = db.query(Allocation).filter(
        Allocation.asset_id == asset_id,
        Allocation.returned_at == None
    ).first()
    if not allocation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active allocation found for this asset"
        )
    return allocation
