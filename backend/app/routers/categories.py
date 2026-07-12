from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse
from app.routers.deps import get_current_user, RoleChecker
from app.models.user import User

router = APIRouter(prefix="/categories", tags=["Categories"])

# Permissions
admin_only = RoleChecker(["Admin"])


def validate_category_fields(fields: dict):
    if fields is None:
        return
    if not isinstance(fields, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="category_specific_fields must be a JSON object"
        )
    if "warranty_months" in fields:
        val = fields["warranty_months"]
        if not isinstance(val, int) or val < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="warranty_months must be a non-negative integer"
            )
    if "requires_maintenance" in fields:
        val = fields["requires_maintenance"]
        if not isinstance(val, bool):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="requires_maintenance must be a boolean"
            )


@router.get("/", response_model=List[CategoryResponse])
def list_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Category).all()


@router.get("/{id}", response_model=CategoryResponse)
def get_category(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    cat = db.query(Category).filter(Category.id == id).first()
    if not cat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    return cat


@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    cat_in: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_only)
):
    # Check if duplicate name
    existing = db.query(Category).filter(Category.name == cat_in.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category with this name already exists"
        )

    # Validate category-specific fields
    if cat_in.category_specific_fields is not None:
        validate_category_fields(cat_in.category_specific_fields)

    cat = Category(
        name=cat_in.name,
        description=cat_in.description,
        category_specific_fields=cat_in.category_specific_fields,
        is_active=cat_in.is_active if cat_in.is_active is not None else True
    )
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


@router.put("/{id}", response_model=CategoryResponse)
def update_category(
    id: int,
    cat_in: CategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_only)
):
    cat = db.query(Category).filter(Category.id == id).first()
    if not cat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )

    if cat_in.name is not None:
        existing = db.query(Category).filter(Category.name == cat_in.name, Category.id != id).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category with this name already exists"
            )
        cat.name = cat_in.name

    if cat_in.description is not None:
        cat.description = cat_in.description

    if cat_in.category_specific_fields is not None:
        validate_category_fields(cat_in.category_specific_fields)
        cat.category_specific_fields = cat_in.category_specific_fields

    if cat_in.is_active is not None:
        cat.is_active = cat_in.is_active

    db.commit()
    db.refresh(cat)
    return cat


@router.delete("/{id}", response_model=CategoryResponse)
def deactivate_category(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_only)
):
    cat = db.query(Category).filter(Category.id == id).first()
    if not cat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )

    cat.is_active = False
    db.commit()
    db.refresh(cat)
    return cat
