from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.database import get_db
from app.models.employee import Employee
from app.models.role import Role
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    SignupRequest,
    TokenResponse,
    UserResponse,
)


router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"]
)


@router.post(
    "/signup",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
def signup(
    signup_data: SignupRequest,
    db: Session = Depends(get_db)
):
    existing_user = db.query(User).filter(
        User.email == signup_data.email
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists"
        )

    employee_role = db.query(Role).filter(
        Role.name == "Employee"
    ).first()

    if employee_role is None:
        employee_role = Role(name="Employee")
        db.add(employee_role)
        db.flush()

    new_user = User(
        name=signup_data.name,
        email=signup_data.email,
        hashed_password=hash_password(signup_data.password),
        role_id=employee_role.id,
        is_active=True
    )

    db.add(new_user)
    db.flush()

    new_employee = Employee(
        user_id=new_user.id,
        employee_code=f"EMP-{new_user.id:04d}",
        is_active=True
    )

    db.add(new_employee)
    db.commit()
    db.refresh(new_user)

    return UserResponse(
        id=new_user.id,
        name=new_user.name,
        email=new_user.email,
        role=new_user.role.name,
        is_active=new_user.is_active
    )


@router.post(
    "/login",
    response_model=TokenResponse
)
def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(
        User.email == login_data.email
    ).first()

    if user is None or not verify_password(
        login_data.password,
        user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    access_token = create_access_token(
        data={"sub": str(user.id)}
    )

    return TokenResponse(
        access_token=access_token
    )


@router.get(
    "/me",
    response_model=UserResponse
)
def get_authenticated_user(
    current_user: User = Depends(get_current_user)
):
    return UserResponse(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        role=current_user.role.name,
        is_active=current_user.is_active
    )