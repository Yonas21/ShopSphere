from sqlalchemy.orm import Session
from models.user import User
from schemas.user import UserCreate, UserUpdate, PasswordChange
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def create_user(db: Session, user: UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        username=user.username,
        hashed_password=hashed_password,
        role=user.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def authenticate_user(db: Session, username: str, password: str):
    user = get_user_by_username(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, secret_key: str = None, algorithm: str = None, expires_delta: Optional[timedelta] = None):
    from auth import settings
    secret_key = secret_key or settings.secret_key
    algorithm = algorithm or settings.algorithm
    
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=algorithm)
    return encoded_jwt

def verify_token(token: str) -> Optional[dict]:
    """Verify JWT token and return payload if valid."""
    from auth import settings
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except JWTError:
        return None

def update_user_profile(db: Session, user_id: int, user_update: UserUpdate):
    """Update user profile information"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None
    
    # Check if email is being updated and already exists
    if user_update.email and user_update.email != user.email:
        existing_email = get_user_by_email(db, user_update.email)
        if existing_email:
            raise ValueError("Email already registered")
        user.email = user_update.email
    
    # Check if username is being updated and already exists
    if user_update.username and user_update.username != user.username:
        existing_username = get_user_by_username(db, user_update.username)
        if existing_username:
            raise ValueError("Username already taken")
        user.username = user_update.username
    
    db.commit()
    db.refresh(user)
    return user

def change_password(db: Session, user_id: int, password_change: PasswordChange):
    """Change user password"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None
    
    # Verify current password
    if not verify_password(password_change.current_password, user.hashed_password):
        raise ValueError("Current password is incorrect")
    
    # Update to new password
    user.hashed_password = get_password_hash(password_change.new_password)
    db.commit()
    db.refresh(user)
    return user
