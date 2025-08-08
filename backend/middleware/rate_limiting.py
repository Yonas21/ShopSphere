"""
Rate limiting middleware for FastAPI application
"""
import time
import redis
from typing import Callable, Optional
from fastapi import HTTPException, Request, Response
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
import logging
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)

class RateLimitSettings(BaseSettings):
    rate_limit_requests: int = 100
    rate_limit_window: int = 60
    redis_url: str = "redis://localhost:6379"
    
    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        extra = 'ignore'

settings = RateLimitSettings()

# Try to connect to Redis, fall back to in-memory storage
try:
    redis_client = redis.Redis.from_url(settings.redis_url, decode_responses=True)
    redis_client.ping()  # Test connection
    logger.info("Connected to Redis for rate limiting")
except (redis.ConnectionError, redis.TimeoutError):
    logger.warning("Redis not available, using in-memory rate limiting")
    redis_client = None

# Create limiter with Redis or in-memory storage
if redis_client:
    limiter = Limiter(
        key_func=get_remote_address,
        storage_uri=settings.redis_url
    )
else:
    # Fallback to in-memory storage
    limiter = Limiter(
        key_func=get_remote_address
    )

def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """Custom handler for rate limit exceeded"""
    logger.warning(f"Rate limit exceeded for {get_remote_address(request)}")
    return JSONResponse(
        status_code=429,
        content={
            "error": "Rate limit exceeded",
            "message": f"Too many requests. Limit: {exc.detail}",
            "retry_after": exc.retry_after
        }
    )

def get_rate_limiter():
    """Get the rate limiter instance"""
    return limiter

def get_client_identifier(request: Request) -> str:
    """
    Get client identifier for rate limiting.
    Uses X-Forwarded-For header if behind proxy, otherwise uses direct IP.
    """
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take the first IP in the chain
        return forwarded_for.split(",")[0].strip()
    
    client_host = request.client.host if request.client else "unknown"
    return client_host

class CustomRateLimitMiddleware:
    """
    Custom rate limiting middleware with enhanced features
    """
    def __init__(self, app, limiter: Limiter):
        self.app = app
        self.limiter = limiter
        self.in_memory_store = {}  # Fallback for when Redis is not available
    
    async def __call__(self, request: Request, call_next: Callable):
        # Skip rate limiting for health checks and static files
        if request.url.path in ["/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        if request.url.path.startswith("/static/"):
            return await call_next(request)
        
        client_id = get_client_identifier(request)
        
        # Check rate limit
        try:
            await self._check_rate_limit(request, client_id)
        except RateLimitExceeded as e:
            return rate_limit_exceeded_handler(request, e)
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        self._add_rate_limit_headers(response, client_id)
        
        return response
    
    async def _check_rate_limit(self, request: Request, client_id: str):
        """Check if client has exceeded rate limit"""
        if not redis_client:
            # Use in-memory fallback
            await self._check_in_memory_limit(client_id)
        else:
            # Use Redis-based rate limiting
            await self._check_redis_limit(client_id)
    
    async def _check_in_memory_limit(self, client_id: str):
        """In-memory rate limiting fallback"""
        current_time = time.time()
        window_start = current_time - settings.rate_limit_window
        
        if client_id not in self.in_memory_store:
            self.in_memory_store[client_id] = []
        
        # Remove old requests outside the window
        self.in_memory_store[client_id] = [
            req_time for req_time in self.in_memory_store[client_id]
            if req_time > window_start
        ]
        
        # Check if limit exceeded
        if len(self.in_memory_store[client_id]) >= settings.rate_limit_requests:
            oldest_request = min(self.in_memory_store[client_id])
            retry_after = int(oldest_request + settings.rate_limit_window - current_time) + 1
            raise RateLimitExceeded(
                detail=f"{settings.rate_limit_requests}/{settings.rate_limit_window}seconds",
                retry_after=retry_after
            )
        
        # Add current request
        self.in_memory_store[client_id].append(current_time)
    
    async def _check_redis_limit(self, client_id: str):
        """Redis-based rate limiting"""
        key = f"rate_limit:{client_id}"
        current_time = time.time()
        window_start = current_time - settings.rate_limit_window
        
        # Remove old requests
        redis_client.zremrangebyscore(key, 0, window_start)
        
        # Count current requests
        current_requests = redis_client.zcard(key)
        
        if current_requests >= settings.rate_limit_requests:
            # Get the oldest request to calculate retry_after
            oldest_requests = redis_client.zrange(key, 0, 0, withscores=True)
            if oldest_requests:
                oldest_time = oldest_requests[0][1]
                retry_after = int(oldest_time + settings.rate_limit_window - current_time) + 1
            else:
                retry_after = settings.rate_limit_window
                
            raise RateLimitExceeded(
                detail=f"{settings.rate_limit_requests}/{settings.rate_limit_window}seconds",
                retry_after=retry_after
            )
        
        # Add current request
        redis_client.zadd(key, {str(current_time): current_time})
        redis_client.expire(key, settings.rate_limit_window)
    
    def _add_rate_limit_headers(self, response: Response, client_id: str):
        """Add rate limit information to response headers"""
        try:
            if redis_client:
                key = f"rate_limit:{client_id}"
                current_requests = redis_client.zcard(key)
            else:
                current_requests = len(self.in_memory_store.get(client_id, []))
            
            remaining = max(0, settings.rate_limit_requests - current_requests)
            
            response.headers["X-RateLimit-Limit"] = str(settings.rate_limit_requests)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str(int(time.time() + settings.rate_limit_window))
            
        except Exception as e:
            logger.error(f"Error adding rate limit headers: {e}")

# Specific rate limits for different endpoints
auth_limiter = Limiter(
    key_func=get_remote_address
)

upload_limiter = Limiter(
    key_func=get_remote_address
)

api_limiter = limiter  # General API rate limit