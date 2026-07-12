from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.models.asset import Asset
from app.models.category import Category
from app.models.asset_history import AssetHistory
from app.schemas.asset import AssetCreate, AssetUpdate, AssetResponse
from app.schemas.asset_history import AssetHistoryResponse
from app.routers.deps import get_current_user, RoleChecker

router = APIRouter(prefix="/assets", tags=["Assets"])

# Permissions
admin_or_manager = RoleChecker(["Admin", "Asset Manager"])


@router.get("/", response_model=List[AssetResponse])
def list_assets(
    q: Optional[str] = Query(None, description="Search query for name, description, tag, or serial number"),
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    status: Optional[str] = Query(None, description="Filter by status (Available, Allocated, Reserved, Under Maintenance, Lost, Retired, Disposed)"),
    is_bookable: Optional[bool] = Query(None, description="Filter by bookable flag"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1),
    db: Session = Depends(get_db)
):
    query = db.query(Asset)
    
    if q:
        query = query.filter(
            Asset.name.ilike(f"%{q}%") | 
            Asset.description.ilike(f"%{q}%") | 
            Asset.asset_tag.ilike(f"%{q}%") |
            Asset.serial_number.ilike(f"%{q}%")
        )
        
    if category_id is not None:
        query = query.filter(Asset.category_id == category_id)
        
    if status:
        query = query.filter(Asset.status == status)
        
    if is_bookable is not None:
        query = query.filter(Asset.is_bookable == is_bookable)
        
    return query.offset(skip).limit(limit).all()


@router.get("/{id}", response_model=AssetResponse)
def get_asset(id: int, db: Session = Depends(get_db)):
    asset = db.query(Asset).filter(Asset.id == id).first()
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    return asset


@router.post("/", response_model=AssetResponse, status_code=status.HTTP_201_CREATED)
def register_asset(
    asset_in: AssetCreate,
    db: Session = Depends(get_db),
    current_user=Depends(admin_or_manager)
):
    # Verify Category exists
    category = db.query(Category).filter(Category.id == asset_in.category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )

    # Generate Asset Tag if not provided
    tag = asset_in.asset_tag
    if not tag:
        # Generate AST-XXXX tag
        count = db.query(Asset).count()
        tag = f"AST-{count + 1:04d}"
        # Ensure uniqueness
        while db.query(Asset).filter(Asset.asset_tag == tag).first() is not None:
            count += 1
            tag = f"AST-{count + 1:04d}"

    # Check manual tag uniqueness
    else:
        existing = db.query(Asset).filter(Asset.asset_tag == tag).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Asset tag '{tag}' already exists"
            )

    asset = Asset(
        name=asset_in.name,
        asset_tag=tag,
        description=asset_in.description,
        category_id=asset_in.category_id,
        image_url=asset_in.image_url,
        document_urls=asset_in.document_urls,
        is_bookable=asset_in.is_bookable,
        status=asset_in.status or "Available",
        serial_number=asset_in.serial_number,
        purchase_date=asset_in.purchase_date,
        purchase_cost=asset_in.purchase_cost,
        warranty_expiry=asset_in.warranty_expiry,
        category_specific_data=asset_in.category_specific_data
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)

    # Log History
    history = AssetHistory(
        asset_id=asset.id,
        action="registration",
        action_by_id=current_user.id,
        action_date=datetime.utcnow(),
        notes="Asset registered in system"
    )
    db.add(history)
    db.commit()

    return asset


@router.put("/{id}", response_model=AssetResponse)
def update_asset(
    id: int,
    asset_in: AssetUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(admin_or_manager)
):
    asset = db.query(Asset).filter(Asset.id == id).first()
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")

    old_status = asset.status
    
    # Update fields
    for field, value in asset_in.dict(exclude_unset=True).items():
        if field == "category_id":
            category = db.query(Category).filter(Category.id == value).first()
            if not category:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
        setattr(asset, field, value)

    db.commit()
    db.refresh(asset)

    # Log status change history if status updated
    if asset.status != old_status:
        history = AssetHistory(
            asset_id=asset.id,
            action="status_change",
            action_by_id=current_user.id,
            action_date=datetime.utcnow(),
            notes=f"Status changed from {old_status} to {asset.status}"
        )
        db.add(history)
        db.commit()

    return asset


@router.get("/{id}/history", response_model=List[AssetHistoryResponse])
def get_asset_history(id: int, db: Session = Depends(get_db)):
    # Verify asset exists
    asset = db.query(Asset).filter(Asset.id == id).first()
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")

    return db.query(AssetHistory).filter(AssetHistory.asset_id == id).order_by(AssetHistory.action_date.desc()).all()
