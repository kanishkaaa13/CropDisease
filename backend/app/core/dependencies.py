"""
Authentication dependencies for FastAPI routes.
"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.db.connection import get_db
from app.db.models import User, UserRole
from app.core.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get the current authenticated user from JWT token.
    
    Raises:
        HTTPException 401: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    email = decode_access_token(token)
    if email is None:
        raise credentials_exception
    
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    
    return user


def require_role(required_role: UserRole):
    """
    Dependency factory to require a specific user role.
    
    Args:
        required_role: The UserRole required to access the route
        
    Returns:
        A dependency function that checks the user's role
    """
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. {required_role.value} role required."
            )
        return current_user
    
    return role_checker


def require_officer(current_user: User = Depends(get_current_user)) -> User:
    """
    Convenience dependency to require officer role.
    """
    if current_user.role != UserRole.officer:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Officer role required."
        )
    return current_user


def require_farmer(current_user: User = Depends(get_current_user)) -> User:
    """
    Convenience dependency to require farmer role.
    """
    if current_user.role != UserRole.farmer:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Farmer role required."
        )
    return current_user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    Convenience dependency to require admin role.
    """
    if current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Admin role required."
        )
    return current_user
