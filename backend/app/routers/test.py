from fastapi import APIRouter, Depends
from app.core.dependencies import RoleChecker
from app.models.user import User
from app.schemas.auth import UserResponse

router = APIRouter(
    prefix="/api/test",
    tags=["RBAC Testing"]
)

@router.get("/employee", response_model=UserResponse)
def test_employee(
    current_user: User = Depends(RoleChecker(["Admin", "Asset Manager", "Department Head", "Employee"]))
):
    return UserResponse(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        role=current_user.role.name,
        is_active=current_user.is_active
    )

@router.get("/department-head", response_model=UserResponse)
def test_department_head(
    current_user: User = Depends(RoleChecker(["Admin", "Department Head"]))
):
    return UserResponse(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        role=current_user.role.name,
        is_active=current_user.is_active
    )

@router.get("/asset-manager", response_model=UserResponse)
def test_asset_manager(
    current_user: User = Depends(RoleChecker(["Admin", "Asset Manager"]))
):
    return UserResponse(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        role=current_user.role.name,
        is_active=current_user.is_active
    )

@router.get("/admin", response_model=UserResponse)
def test_admin(
    current_user: User = Depends(RoleChecker(["Admin"]))
):
    return UserResponse(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        role=current_user.role.name,
        is_active=current_user.is_active
    )
