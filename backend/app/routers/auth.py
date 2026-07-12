from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import timedelta

from app.database import get_db
from app.core.security import create_access_token, verify_password, get_password_hash, hash_password
from app.models.user import User
from app.models.employee import Employee
from app.models.role import Role
from app.schemas.auth import Token, TokenResponse, LoginRequest, SignupRequest, UserResponse, ForgotPasswordRequest, ForgotPasswordResponse, ResetPasswordRequest
from app.routers.deps import get_current_user
from app.core.dependencies import security

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def signup(signup_data: SignupRequest, db: Session = Depends(get_db)):
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == signup_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )
    
    # Get or create Employee role
    employee_role = db.query(Role).filter(Role.name == "Employee").first()
    if employee_role is None:
        employee_role = Role(name="Employee")
        db.add(employee_role)
        db.flush()
    
    # Create user
    db_user = User(
        name=signup_data.name,
        email=signup_data.email,
        hashed_password=get_password_hash(signup_data.password),
        role_id=employee_role.id,
        is_active=True,
    )
    db.add(db_user)
    db.flush()
    
    # Create employee record
    new_employee = Employee(
        user_id=db_user.id,
        employee_code=f"EMP-{db_user.id:04d}",
        is_active=True
    )
    db.add(new_employee)
    db.commit()
    db.refresh(db_user)
    
    return UserResponse(
        id=db_user.id,
        name=db_user.name,
        email=db_user.email,
        role=db_user.role.name,
        is_active=db_user.is_active
    )


@router.post("/login", response_model=TokenResponse)
def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    # JSON-based login endpoint for frontend requests
    user = db.query(User).filter(User.email == login_data.email).first()
    if user is None or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
        
    access_token = create_access_token(subject=user.id)
    return TokenResponse(access_token=access_token)


@router.post("/login-form", response_model=Token)
def login_form(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    # Form-based login endpoint for Swagger UI OAuth2 authorization
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password"
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account"
        )
        
    access_token = create_access_token(subject=user.id)
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
def get_authenticated_user(current_user: User = Depends(get_current_user)):
    return UserResponse(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        role=current_user.role.name,
        is_active=current_user.is_active
    )


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
def forgot_password(
    forgot_data: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == forgot_data.email).first()
    
    expires_delta = timedelta(minutes=15)
    
    if user:
        token = create_access_token(
            data={"sub": str(user.id), "purpose": "password_reset"},
            expires_delta=expires_delta
        )
    else:
        # Mock token to prevent account enumeration
        token = create_access_token(
            data={"sub": "0", "purpose": "password_reset"},
            expires_delta=expires_delta
        )
        
    return ForgotPasswordResponse(
        message="If this email is registered, a password reset link/token has been sent.",
        reset_token=token
    )


@router.post("/reset-password")
def reset_password(
    reset_data: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    from app.core.security import decode_access_token
    
    payload = decode_access_token(reset_data.token)
    if payload is None or payload.get("purpose") != "password_reset":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
        
    user_id = payload.get("sub")
    if user_id is None or user_id == "0":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
        
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
        
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
        
    user.hashed_password = hash_password(reset_data.new_password)
    db.commit()
    return {"message": "Password has been reset successfully"}


@router.post("/logout")
def logout(
    current_user: User = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    from app.core.dependencies import token_blacklist
    
    token = credentials.credentials
    token_blacklist.add(token)
    return {"message": "Successfully logged out"}
