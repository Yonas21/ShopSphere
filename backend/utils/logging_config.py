"""
Centralized logging configuration for the application
"""
import logging
import logging.handlers
import sys
import json
from datetime import datetime
from typing import Dict, Any
from pathlib import Path
from pydantic_settings import BaseSettings

class LoggingSettings(BaseSettings):
    log_level: str = "INFO"
    log_file: str = "backend.log"
    log_format: str = "json"  # json or text
    log_max_bytes: int = 10 * 1024 * 1024  # 10MB
    log_backup_count: int = 5
    
    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        extra = 'ignore'

settings = LoggingSettings()

class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, 'extra_fields'):
            log_entry.update(record.extra_fields)
        
        # Add request context if available
        if hasattr(record, 'request_id'):
            log_entry["request_id"] = record.request_id
        
        if hasattr(record, 'user_id'):
            log_entry["user_id"] = record.user_id
        
        if hasattr(record, 'ip_address'):
            log_entry["ip_address"] = record.ip_address
        
        return json.dumps(log_entry)

class TextFormatter(logging.Formatter):
    """Enhanced text formatter"""
    
    def __init__(self):
        super().__init__(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s [%(filename)s:%(lineno)d]',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

def setup_logging():
    """Configure logging for the application"""
    
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    log_file_path = log_dir / settings.log_file
    
    # Set logging level
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_file_path,
        maxBytes=settings.log_max_bytes,
        backupCount=settings.log_backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(level)
    
    # Set formatters
    if settings.log_format.lower() == "json":
        formatter = JSONFormatter()
    else:
        formatter = TextFormatter()
    
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    # Add handlers to root logger
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    # Configure specific loggers
    
    # Reduce noise from external libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    
    # Application loggers
    logging.getLogger("app").setLevel(level)
    logging.getLogger("security").setLevel(logging.INFO)
    logging.getLogger("auth").setLevel(logging.INFO)
    
    logger = logging.getLogger("app.logging")
    logger.info("Logging configured successfully", extra={
        "extra_fields": {
            "log_level": settings.log_level,
            "log_file": str(log_file_path),
            "log_format": settings.log_format
        }
    })

def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name"""
    return logging.getLogger(name)

class LogContext:
    """Context manager for adding extra fields to log messages"""
    
    def __init__(self, **kwargs):
        self.extra_fields = kwargs
        self.old_factory = logging.getLogRecordFactory()
    
    def __enter__(self):
        def record_factory(*args, **factory_kwargs):
            record = self.old_factory(*args, **factory_kwargs)
            record.extra_fields = self.extra_fields
            return record
        
        logging.setLogRecordFactory(record_factory)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        logging.setLogRecordFactory(self.old_factory)

class SecurityLogger:
    """Specialized logger for security events"""
    
    def __init__(self):
        self.logger = get_logger("security")
    
    def log_auth_attempt(self, username: str, ip_address: str, success: bool, **kwargs):
        """Log authentication attempts"""
        level = logging.INFO if success else logging.WARNING
        message = f"Authentication {'successful' if success else 'failed'} for user: {username}"
        
        extra_fields = {
            "event_type": "authentication",
            "username": username,
            "ip_address": ip_address,
            "success": success,
            **kwargs
        }
        
        self.logger.log(level, message, extra={"extra_fields": extra_fields})
    
    def log_permission_denied(self, username: str, resource: str, ip_address: str, **kwargs):
        """Log permission denied events"""
        message = f"Permission denied for user {username} accessing {resource}"
        
        extra_fields = {
            "event_type": "permission_denied",
            "username": username,
            "resource": resource,
            "ip_address": ip_address,
            **kwargs
        }
        
        self.logger.warning(message, extra={"extra_fields": extra_fields})
    
    def log_rate_limit_exceeded(self, ip_address: str, endpoint: str, **kwargs):
        """Log rate limit exceeded events"""
        message = f"Rate limit exceeded for IP {ip_address} on endpoint {endpoint}"
        
        extra_fields = {
            "event_type": "rate_limit_exceeded",
            "ip_address": ip_address,
            "endpoint": endpoint,
            **kwargs
        }
        
        self.logger.warning(message, extra={"extra_fields": extra_fields})
    
    def log_suspicious_activity(self, description: str, ip_address: str, **kwargs):
        """Log suspicious activities"""
        message = f"Suspicious activity detected: {description}"
        
        extra_fields = {
            "event_type": "suspicious_activity",
            "description": description,
            "ip_address": ip_address,
            **kwargs
        }
        
        self.logger.error(message, extra={"extra_fields": extra_fields})

# Global instances
security_logger = SecurityLogger()

def log_api_call(endpoint: str, method: str, status_code: int, user_id: str = None, ip_address: str = None, duration_ms: float = None):
    """Log API calls with performance metrics"""
    logger = get_logger("app.api")
    
    extra_fields = {
        "endpoint": endpoint,
        "method": method,
        "status_code": status_code,
    }
    
    if user_id:
        extra_fields["user_id"] = user_id
    
    if ip_address:
        extra_fields["ip_address"] = ip_address
    
    if duration_ms is not None:
        extra_fields["duration_ms"] = duration_ms
    
    level = logging.INFO
    if status_code >= 400:
        level = logging.WARNING
    if status_code >= 500:
        level = logging.ERROR
    
    message = f"{method} {endpoint} - {status_code}"
    if duration_ms is not None:
        message += f" ({duration_ms:.2f}ms)"
    
    logger.log(level, message, extra={"extra_fields": extra_fields})

def log_database_operation(operation: str, table: str, success: bool, duration_ms: float = None, error: str = None):
    """Log database operations"""
    logger = get_logger("app.database")
    
    extra_fields = {
        "operation": operation,
        "table": table,
        "success": success,
    }
    
    if duration_ms is not None:
        extra_fields["duration_ms"] = duration_ms
    
    if error:
        extra_fields["error"] = error
    
    level = logging.INFO if success else logging.ERROR
    message = f"Database {operation} on {table} - {'SUCCESS' if success else 'FAILED'}"
    
    if duration_ms is not None:
        message += f" ({duration_ms:.2f}ms)"
    
    logger.log(level, message, extra={"extra_fields": extra_fields})