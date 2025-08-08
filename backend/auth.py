from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from database.sql_database import get_db
from crud.user import get_user_by_username
from schemas.user import TokenData
from models.user import User, UserRole
from pydantic_settings import BaseSettings
from typing import List
from utils.logging_config import security_logger
from utils.validation import sanitize_string
import logging

logger = logging.getLogger("app.auth")

class Settings(BaseSettings):
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        extra = 'ignore'

settings = Settings()

security = HTTPBearer()

__all__ = ['get_current_user', 'get_current_active_user', 'settings']

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security), 
    db: Session = Depends(get_db),
    request: Request = None
):
    """Get current user from JWT token with enhanced security logging"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Get client IP for logging
    client_ip = "unknown"
    if request:
        client_ip = getattr(request.state, 'client_ip', 
                          request.client.host if request.client else "unknown")
    
    try:
        # Decode and validate JWT token
        payload = jwt.decode(
            credentials.credentials, 
            settings.secret_key, 
            algorithms=[settings.algorithm]
        )
        
        username: str = payload.get("sub")
        if username is None:
            security_logger.log_auth_attempt("unknown", client_ip, False, reason="Missing username in token")
            raise credentials_exception
        
        # Sanitize username from token
        username = sanitize_string(username)
        token_data = TokenData(username=username)
        
    except JWTError as e:
        logger.warning(f"JWT validation failed from {client_ip}: {str(e)}")
        security_logger.log_auth_attempt("unknown", client_ip, False, reason="Invalid JWT token")
        raise credentials_exception
    
    # Get user from database
    user = get_user_by_username(db, username=token_data.username)
    if user is None:
        security_logger.log_auth_attempt(token_data.username, client_ip, False, reason="User not found")
        raise credentials_exception
    
    # Log successful authentication
    security_logger.log_auth_attempt(user.username, client_ip, True)
    
    # Store user info in request state for monitoring
    if request:
        request.state.user_id = str(user.id)
    
    return user

def get_current_active_user(current_user: User = Depends(get_current_user), request: Request = None):
    """Get current active user with activity logging"""
    client_ip = "unknown"
    if request:
        client_ip = getattr(request.state, 'client_ip', 
                          request.client.host if request.client else "unknown")
    
    if not current_user.is_active:
        security_logger.log_auth_attempt(
            current_user.username, 
            client_ip, 
            False, 
            reason="User account inactive"
        )
        raise HTTPException(status_code=400, detail="Inactive user")
    
    return current_user

def require_roles(allowed_roles: List[UserRole]):
    """Role-based access control with security logging"""
    def role_checker(
        current_user: User = Depends(get_current_active_user),
        request: Request = None
    ):
        if current_user.role not in allowed_roles:
            client_ip = "unknown"
            if request:
                client_ip = getattr(request.state, 'client_ip', 
                                  request.client.host if request.client else "unknown")
            
            # Log permission denied
            resource = request.url.path if request else "unknown"
            security_logger.log_permission_denied(
                current_user.username, 
                resource, 
                client_ip,
                required_roles=[role.value for role in allowed_roles],
                user_role=current_user.role.value
            )
            
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {[role.value for role in allowed_roles]}"
            )
        return current_user
    return role_checker

def get_admin_user(current_user: User = Depends(require_roles([UserRole.ADMIN]))):
    return current_user

def get_customer_user(current_user: User = Depends(require_roles([UserRole.CUSTOMER]))):
    return current_user

def get_admin_or_customer_user(current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.CUSTOMER]))):
    return current_user

# Alias for backwards compatibility
require_admin = get_admin_user