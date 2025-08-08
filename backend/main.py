from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from pydantic_settings import BaseSettings
from typing import List
import logging

# Import database and models
from database.sql_database import engine, Base, get_db
from database.mongodb import connect_to_mongo, close_mongo_connection
from api import users, items, cart, upload, payments
from models import user, item, payment

# Import security and monitoring
from middleware.rate_limiting import limiter, get_rate_limiter, CustomRateLimitMiddleware
from middleware.monitoring import MonitoringMiddleware, health_monitor, metrics_collector
from utils.logging_config import setup_logging, get_logger, security_logger
from utils.validation import ValidationError, create_validation_error
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

# Setup logging first
setup_logging()
logger = get_logger("app.main")

class Settings(BaseSettings):
    # Database
    database_url: str
    mongodb_url: str
    mongodb_database: str
    
    # Security
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # CORS
    allowed_origins: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # Rate limiting
    rate_limit_requests: int = 100
    rate_limit_window: int = 60
    
    # Environment
    environment: str = "development"
    debug: bool = True
    
    # Trusted hosts (for production)
    trusted_hosts: List[str] = ["localhost", "127.0.0.1", "*.yourdomain.com"]
    
    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        extra = 'ignore'

settings = Settings()

# Configure FastAPI app
app = FastAPI(
    title="Secure FastAPI E-Commerce API",
    description="A secure full-stack e-commerce application with comprehensive security features",
    version="1.0.0",
    docs_url="/docs" if settings.debug else None,  # Disable docs in production
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/openapi.json" if settings.debug else None,
)

# Security Middleware (order matters!)
if settings.environment == "production":
    app.add_middleware(
        TrustedHostMiddleware, 
        allowed_hosts=settings.trusted_hosts
    )

# Monitoring middleware (should be early in the chain)
app.add_middleware(MonitoringMiddleware)

# Rate limiting middleware
rate_limiter = get_rate_limiter()
app.state.limiter = rate_limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware with specific configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # Specific methods only
    allow_headers=[
        "Accept",
        "Accept-Language",
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "X-CSRF-Token",
    ],  # Specific headers only
    expose_headers=["X-Request-ID", "X-Response-Time"],
    max_age=600,  # Cache preflight requests for 10 minutes
)

# Create SQLAlchemy tables
Base.metadata.create_all(bind=engine)

# Global exception handlers
@app.exception_handler(ValidationError)
async def validation_exception_handler(request, exc):
    logger.warning(f"Validation error on {request.url.path}: {str(exc)}")
    return JSONResponse(
        status_code=422,
        content={"error": "Validation Error", "message": str(exc)}
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    logger.warning(f"HTTP error {exc.status_code} on {request.url.path}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": "HTTP Error", "message": exc.detail}
    )

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unexpected error on {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error", 
            "message": "An unexpected error occurred" if settings.environment == "production" else str(exc)
        }
    )

# Include routers with rate limiting
app.include_router(users.router, prefix="/api")
app.include_router(items.router, prefix="/api")
app.include_router(cart.router, prefix="/api")
app.include_router(upload.router, prefix="/api")
app.include_router(payments.router)

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    logger.info("Application startup initiated")
    try:
        await connect_to_mongo()
        logger.info("MongoDB connection established")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        # Don't fail startup if MongoDB is not available (it's optional)
    
    logger.info("Application startup completed")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutdown initiated")
    try:
        await close_mongo_connection()
        logger.info("MongoDB connection closed")
    except Exception as e:
        logger.error(f"Error closing MongoDB connection: {e}")
    
    logger.info("Application shutdown completed")

# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Welcome message"""
    return {
        "message": "Secure FastAPI E-Commerce API",
        "version": "1.0.0",
        "status": "running",
        "environment": settings.environment
    }

# Enhanced health check endpoint
@app.get("/health", tags=["Health"])
async def health_check(db: get_db = Depends()):
    """Comprehensive health check"""
    health_status = {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z",  # Will be replaced with actual timestamp
        "version": "1.0.0",
        "environment": settings.environment,
        "checks": {}
    }
    
    # Check database connectivity
    try:
        db_healthy = await health_monitor.check_database_health(db)
        health_status["checks"]["database"] = "healthy" if db_healthy else "unhealthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health_status["checks"]["database"] = "unhealthy"
        health_status["status"] = "degraded"
    
    # Check Redis connectivity (if available)
    try:
        redis_healthy = await health_monitor.check_redis_health(None)  # Will implement Redis client
        health_status["checks"]["redis"] = "healthy" if redis_healthy else "not_configured"
    except Exception:
        health_status["checks"]["redis"] = "not_configured"
    
    # Add system metrics if available
    try:
        metrics = health_monitor.get_system_metrics()
        if metrics:
            health_status["system"] = metrics
    except Exception as e:
        logger.debug(f"System metrics not available: {e}")
    
    # Update timestamp
    from datetime import datetime
    health_status["timestamp"] = datetime.utcnow().isoformat() + "Z"
    
    return health_status

# Metrics endpoint (for monitoring)
@app.get("/metrics", tags=["Monitoring"])
async def get_metrics():
    """Get application metrics"""
    if settings.environment == "production":
        # In production, you might want to protect this endpoint
        # or use a proper metrics system like Prometheus
        raise HTTPException(status_code=404, detail="Not found")
    
    return metrics_collector.get_metrics_summary()

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request, call_next):
    """Add security headers to all responses"""
    response = await call_next(request)
    
    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    if settings.environment == "production":
        # HSTS header for production
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # CSP header (adjust based on your frontend needs)
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://js.stripe.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self' https://api.stripe.com; "
            "frame-src https://js.stripe.com https://www.paypal.com; "
        )
        response.headers["Content-Security-Policy"] = csp
    
    return response

# Rate limiting decorators for specific endpoints can be applied in individual routers
# The global rate limiting is handled by the middleware
