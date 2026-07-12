from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Optional

from app.database import get_db
from app.models.transfer import Transfer
from app.models.asset import Asset
from app.models.allocation import Allocation
from app.models.employee import Employee
from app.models.asset_history import AssetHistory
from app.schemas.transfer import TransferRequest, TransferAction, TransferResponse
from app.routers.deps import get_current_user, get_current_employee, RoleChecker

router = APIRouter(prefix="/transfers", tags=["Transfers"])

# Permissions
admin_or_manager = RoleChecker(["Admin", "Asset Manager"])
dept_head_or_above = RoleChecker(["Admin", "Asset Manager", "Department Head"])


@router.get("/", response_model=List[TransferResponse])
def list_transfers(
    status: Optional[str] = Query(None, description="Filter by transfer status: 'pending', 'approved', 'rejected'"),
    db: Session = Depends(get_db)
):
    query = db.query(Transfer)
    if status:
        query = query.filter(Transfer.status == status)
    return query.all()


@router.post("/", response_model=TransferResponse, status_code=status.HTTP_201_CREATED)
def request_transfer(
    transfer_in: TransferRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    # Verify Asset exists
    asset = db.query(Asset).filter(Asset.id == transfer_in.asset_id).first()
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")

    # Find active allocation to know who it is being transferred FROM
    active_alloc = db.query(Allocation).filter(
        Allocation.asset_id == asset.id,
        Allocation.returned_at == None
    ).first()
    
    if not active_alloc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Asset is not currently allocated to anyone. You can allocate it directly."
        )
        
    if active_alloc.allocated_to_type != "employee" or not active_alloc.employee_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Asset is allocated to a department, not a specific employee. Department allocations must be returned first."
        )

    # Verify target Employee exists and is active
    to_employee = db.query(Employee).filter(Employee.id == transfer_in.to_employee_id).first()
    if not to_employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target employee not found")
    if not to_employee.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Target employee is inactive")

    # Prevent transfer to the same person
    if active_alloc.employee_id == transfer_in.to_employee_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot transfer an asset to the same employee who currently holds it"
        )

    # Check if there is already a pending transfer request for this asset
    pending_transfer = db.query(Transfer).filter(
        Transfer.asset_id == asset.id,
        Transfer.status == "pending"
    ).first()
    if pending_transfer:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="There is already a pending transfer request for this asset"
        )

    # Create Transfer Request
    transfer = Transfer(
        asset_id=transfer_in.asset_id,
        from_employee_id=active_alloc.employee_id,
        to_employee_id=transfer_in.to_employee_id,
        requested_by_id=current_user.id,
        request_date=datetime.utcnow(),
        status="pending",
        notes=transfer_in.notes
    )
    db.add(transfer)
    db.commit()
    db.refresh(transfer)

    # Log History
    history = AssetHistory(
        asset_id=asset.id,
        action="transfer_request",
        action_by_id=current_user.id,
        action_date=datetime.utcnow(),
        notes=f"Transfer requested from employee ID {transfer.from_employee_id} to {transfer.to_employee_id}"
    )
    db.add(history)
    db.commit()

    return transfer


@router.post("/{id}/action", response_model=TransferResponse)
def action_transfer(
    id: int,
    action_in: TransferAction,
    db: Session = Depends(get_db),
    current_user=Depends(dept_head_or_above)
):
    transfer = db.query(Transfer).filter(Transfer.id == id).first()
    if not transfer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transfer request not found")
        
    if transfer.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Transfer request already processed. Current status: {transfer.status}"
        )

    if action_in.status not in ["approved", "rejected"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid action status")

    transfer.status = action_in.status
    transfer.approved_by_id = current_user.id
    transfer.action_date = datetime.utcnow()
    if action_in.notes:
        transfer.notes = (transfer.notes or "") + f" | Action notes: {action_in.notes}"

    asset = transfer.asset

    if action_in.status == "approved":
        # 1. Close current active allocation
        active_alloc = db.query(Allocation).filter(
            Allocation.asset_id == asset.id,
            Allocation.returned_at == None
        ).first()
        
        expected_return = datetime.utcnow() + timedelta(days=30)
        if active_alloc:
            active_alloc.returned_at = datetime.utcnow()
            active_alloc.condition_on_return = "Transferred"
            active_alloc.status = "returned"
            expected_return = active_alloc.expected_return_date  # Inherit expected return date
            
        # 2. Create new allocation
        new_alloc = Allocation(
            asset_id=asset.id,
            allocated_to_type="employee",
            employee_id=transfer.to_employee_id,
            allocated_by_id=current_user.id,
            allocated_at=datetime.utcnow(),
            expected_return_date=expected_return,
            condition_on_allocation="Transferred from previous holder",
            status="active"
        )
        db.add(new_alloc)
        
        # 3. Update asset status
        asset.status = "Allocated"
        
        # Log History
        history = AssetHistory(
            asset_id=asset.id,
            action="transfer_approve",
            action_by_id=current_user.id,
            action_date=datetime.utcnow(),
            notes=f"Transfer approved. Reallocated to Employee ID {transfer.to_employee_id}"
        )
        db.add(history)
        
    else:
        # Transfer rejected
        history = AssetHistory(
            asset_id=asset.id,
            action="transfer_reject",
            action_by_id=current_user.id,
            action_date=datetime.utcnow(),
            notes=f"Transfer request rejected: {action_in.notes or 'No reason provided'}"
        )
        db.add(history)

    db.commit()
    db.refresh(transfer)
    return transfer
