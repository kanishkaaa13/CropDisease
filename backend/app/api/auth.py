"""
Authentication API endpoints.
Handles user registration, login, token management, and user profile.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field, field_validator

from app.db.connection import get_db
from app.db.models import User, UserRole
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

router = APIRouter()

# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


# ---------------------------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------------------------

class UserRegister(BaseModel):
    """Schema for user registration."""
    full_name: str = Field(..., min_length=2, max_length=255, description="User's full name")
    email: EmailStr = Field(..., description="User's email address (must be unique)")
    password: str = Field(..., min_length=8, max_length=100, description="Password (min 8 characters)")
    password_confirmation: Optional[str] = Field(None, min_length=8, max_length=100)
    phone: Optional[str] = Field(None, max_length=20, description="Phone number (optional)")
    role: UserRole = Field(default=UserRole.farmer, description="User role (farmer or officer)")
    district: Optional[str] = Field(None, max_length=100, description="District for officers")
    preferred_language: str = Field(default="en", max_length=10, description="Preferred language code")

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

    @field_validator("password_confirmation")
    @classmethod
    def validate_password_confirmation(cls, v: Optional[str]) -> Optional[str]:
        return v


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., description="User's password")


class UserResponse(BaseModel):
    """Schema for user response (safe data only)."""
    id: str
    full_name: str
    email: str
    phone: Optional[str]
    role: UserRole
    district: Optional[str]
    preferred_language: str
    created_at: datetime

    class Config:
        from_attributes = True


def user_response(user: User) -> UserResponse:
    """Map database field names to the stable frontend authentication shape."""
    return UserResponse(
        id=user.id,
        full_name=user.name,
        email=user.email,
        phone=user.phone,
        role=user.role,
        district=user.district,
        preferred_language=user.language_pref,
        created_at=user.created_at,
    )


def create_user(db: Session, user_data: UserRegister) -> User:
    """Validate and persist a user using the single authentication path."""
    if user_data.password_confirmation is not None and user_data.password != user_data.password_confirmation:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Passwords do not match")
    if user_data.role == UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin registration is not allowed")
    if get_user_by_email(db, user_data.email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    if user_data.phone and db.query(User).filter(User.phone == user_data.phone).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Phone number already registered")

    new_user = User(
        name=user_data.full_name.strip(),
        email=str(user_data.email).lower(),
        phone=user_data.phone,
        password_hash=get_password_hash(user_data.password),
        role=user_data.role,
        district=user_data.district,
        language_pref=user_data.preferred_language,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


class TokenResponse(BaseModel):
    """Schema for token response."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class ErrorResponse(BaseModel):
    """Schema for error responses."""
    detail: str


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email."""
    return db.query(User).filter(User.email == email).first()


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Authenticate user with email and password."""
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


# ---------------------------------------------------------------------------
# Auth Endpoints
# ---------------------------------------------------------------------------

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED, summary="Register a new user")
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """
    Register a new user (farmer or officer).
    
    - **email**: Must be unique across all users
    - **password**: Minimum 8 characters
    - **role**: Either 'farmer' or 'officer'
    - Returns JWT access token and user profile
    """
    new_user = create_user(db, user_data)
    
    # Generate access token
    access_token = create_access_token(data={"sub": new_user.email})
    
    return TokenResponse(
        access_token=access_token,
        user=user_response(new_user)
    )


@router.post("/login", response_model=TokenResponse, summary="Login with email and password")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Login with email and password.
    
    - Returns JWT access token valid for 60 minutes
    - Token must be included in Authorization header as "Bearer <token>"
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.email})
    
    return TokenResponse(
        access_token=access_token,
        user=user_response(user)
    )


@router.get("/me", response_model=UserResponse, summary="Get current user profile")
def get_current_user_profile(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """
    Get the current authenticated user's profile.
    
    Requires valid JWT token in Authorization header.
    """
    from app.core.dependencies import get_current_user
    
    user = get_current_user(token, db)
    return user_response(user)


@router.post("/logout", summary="Logout (client-side token removal)")
def logout():
    """
    Logout endpoint.
    
    Note: JWT tokens are stateless. This endpoint is provided for API completeness.
    Clients should simply discard the token to logout.
    """
    return {"message": "Logout successful. Please discard your access token."}
