"""
Input validation and sanitization utilities
"""
import re
import html
import bleach
from typing import Optional, List, Union
from pydantic import BaseModel, validator, Field
from fastapi import HTTPException, status
import logging

logger = logging.getLogger(__name__)

# Allowed HTML tags and attributes for rich text content
ALLOWED_TAGS = [
    'p', 'br', 'strong', 'em', 'u', 's', 'ul', 'ol', 'li',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote'
]

ALLOWED_ATTRIBUTES = {
    '*': ['class'],
    'a': ['href', 'title'],
    'img': ['src', 'alt', 'title', 'width', 'height']
}

def sanitize_html(content: str) -> str:
    """
    Sanitize HTML content to prevent XSS attacks
    """
    if not content:
        return ""
    
    # Use bleach to clean HTML
    cleaned = bleach.clean(
        content,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        strip=True
    )
    
    return cleaned

def sanitize_string(value: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize a string input
    """
    if not value:
        return ""
    
    # Remove null bytes and control characters
    sanitized = ''.join(char for char in value if ord(char) >= 32 or char in ['\n', '\r', '\t'])
    
    # HTML encode to prevent XSS
    sanitized = html.escape(sanitized)
    
    # Trim whitespace
    sanitized = sanitized.strip()
    
    # Apply length limit
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized

def validate_email(email: str) -> str:
    """
    Validate and sanitize email address
    """
    email = sanitize_string(email, 254)  # RFC 5321 limit
    
    # Basic email regex
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(email_pattern, email):
        raise ValueError("Invalid email format")
    
    return email.lower()

def validate_username(username: str) -> str:
    """
    Validate and sanitize username
    """
    username = sanitize_string(username, 50)
    
    # Username pattern: letters, numbers, underscores, hyphens
    username_pattern = r'^[a-zA-Z0-9_-]+$'
    
    if not re.match(username_pattern, username):
        raise ValueError("Username can only contain letters, numbers, underscores, and hyphens")
    
    if len(username) < 3:
        raise ValueError("Username must be at least 3 characters long")
    
    return username

def validate_password(password: str) -> None:
    """
    Validate password strength
    """
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long")
    
    if len(password) > 128:
        raise ValueError("Password must be less than 128 characters long")
    
    # Check for at least one uppercase, lowercase, digit
    if not re.search(r'[A-Z]', password):
        raise ValueError("Password must contain at least one uppercase letter")
    
    if not re.search(r'[a-z]', password):
        raise ValueError("Password must contain at least one lowercase letter")
    
    if not re.search(r'\d', password):
        raise ValueError("Password must contain at least one digit")
    
    # Check for common weak passwords
    common_passwords = [
        'password', '12345678', 'qwerty', 'abc123', 'password123',
        'admin', 'letmein', 'welcome', 'monkey', '123456789'
    ]
    
    if password.lower() in common_passwords:
        raise ValueError("Password is too common, please choose a stronger password")

def validate_price(price: Union[float, int]) -> float:
    """
    Validate and sanitize price values
    """
    try:
        price = float(price)
    except (ValueError, TypeError):
        raise ValueError("Price must be a valid number")
    
    if price < 0:
        raise ValueError("Price cannot be negative")
    
    if price > 999999.99:
        raise ValueError("Price cannot exceed 999,999.99")
    
    # Round to 2 decimal places
    return round(price, 2)

def validate_quantity(quantity: Union[int, str]) -> int:
    """
    Validate and sanitize quantity values
    """
    try:
        quantity = int(quantity)
    except (ValueError, TypeError):
        raise ValueError("Quantity must be a valid integer")
    
    if quantity < 0:
        raise ValueError("Quantity cannot be negative")
    
    if quantity > 10000:
        raise ValueError("Quantity cannot exceed 10,000")
    
    return quantity

def validate_file_upload(filename: str, file_size: int, allowed_extensions: List[str], max_size_mb: int = 5) -> str:
    """
    Validate file upload parameters
    """
    if not filename:
        raise ValueError("Filename is required")
    
    # Sanitize filename
    filename = sanitize_string(filename, 255)
    
    # Remove path traversal attempts
    filename = filename.replace('..', '').replace('/', '').replace('\\', '')
    
    # Check file extension
    extension = filename.lower().split('.')[-1] if '.' in filename else ''
    
    if extension not in [ext.lower() for ext in allowed_extensions]:
        raise ValueError(f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}")
    
    # Check file size
    max_size_bytes = max_size_mb * 1024 * 1024
    if file_size > max_size_bytes:
        raise ValueError(f"File size too large. Maximum size: {max_size_mb}MB")
    
    return filename

def validate_sql_input(value: str) -> str:
    """
    Basic SQL injection prevention for string inputs
    """
    if not value:
        return ""
    
    # List of potentially dangerous SQL keywords
    dangerous_patterns = [
        r'\b(DROP|DELETE|TRUNCATE|INSERT|UPDATE|EXEC|EXECUTE|SCRIPT)\b',
        r'[\'";]',  # Quote characters
        r'--',      # SQL comments
        r'/\*.*?\*/',  # Multi-line comments
        r'\bOR\s+\d+\s*=\s*\d+\b',  # OR 1=1 patterns
        r'\bUNION\s+SELECT\b',  # UNION SELECT
    ]
    
    value_upper = value.upper()
    
    for pattern in dangerous_patterns:
        if re.search(pattern, value_upper, re.IGNORECASE):
            logger.warning(f"Potential SQL injection attempt detected: {value[:100]}...")
            raise ValueError("Invalid input detected")
    
    return sanitize_string(value)

class ValidationError(Exception):
    """Custom validation error"""
    pass

def create_validation_error(detail: str) -> HTTPException:
    """Create a standardized validation error response"""
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=detail
    )

# Pydantic validators for common fields
class SecureBaseModel(BaseModel):
    """Base model with common security validators"""
    
    @validator('*', pre=True)
    def sanitize_strings(cls, v):
        """Auto-sanitize all string fields"""
        if isinstance(v, str):
            return sanitize_string(v, 1000)  # Default max length
        return v

class SecureUserInput(SecureBaseModel):
    """Secure user input validation"""
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., min_length=5, max_length=254)
    
    @validator('username')
    def validate_username_field(cls, v):
        return validate_username(v)
    
    @validator('email')
    def validate_email_field(cls, v):
        return validate_email(v)

class SecureItemInput(SecureBaseModel):
    """Secure item input validation"""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    price: float = Field(..., gt=0, le=999999.99)
    stock_quantity: int = Field(..., ge=0, le=10000)
    category: str = Field(..., min_length=1, max_length=100)
    
    @validator('name', 'category')
    def validate_text_fields(cls, v):
        return validate_sql_input(v)
    
    @validator('description')
    def validate_description(cls, v):
        if v:
            return sanitize_html(v)
        return v
    
    @validator('price')
    def validate_price_field(cls, v):
        return validate_price(v)
    
    @validator('stock_quantity')
    def validate_quantity_field(cls, v):
        return validate_quantity(v)