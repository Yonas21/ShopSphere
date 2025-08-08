"""
Monitoring and observability middleware
"""
import time
import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import logging
from utils.logging_config import log_api_call, get_logger

logger = get_logger("app.monitoring")

class MonitoringMiddleware(BaseHTTPMiddleware):
    """
    Middleware for monitoring API requests and responses
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Get client IP (handle proxy headers)
        client_ip = self._get_client_ip(request)
        request.state.client_ip = client_ip
        
        # Start timing
        start_time = time.time()
        
        # Log request start
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={
                "extra_fields": {
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "query_params": str(request.query_params),
                    "client_ip": client_ip,
                    "user_agent": request.headers.get("User-Agent", ""),
                }
            }
        )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Get user ID if available (from auth context)
            user_id = getattr(request.state, 'user_id', None)
            
            # Log API call
            log_api_call(
                endpoint=request.url.path,
                method=request.method,
                status_code=response.status_code,
                user_id=user_id,
                ip_address=client_ip,
                duration_ms=duration_ms
            )
            
            # Add monitoring headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"
            
            # Log slow requests (> 1 second)
            if duration_ms > 1000:
                logger.warning(
                    f"Slow request detected: {request.method} {request.url.path} took {duration_ms:.2f}ms",
                    extra={
                        "extra_fields": {
                            "request_id": request_id,
                            "duration_ms": duration_ms,
                            "slow_request": True
                        }
                    }
                )
            
            return response
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            
            logger.error(
                f"Request failed: {request.method} {request.url.path}",
                extra={
                    "extra_fields": {
                        "request_id": request_id,
                        "duration_ms": duration_ms,
                        "error": str(e),
                        "exception_type": type(e).__name__
                    }
                },
                exc_info=True
            )
            
            raise  # Re-raise the exception
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address considering proxy headers"""
        # Check for forwarded headers (when behind proxy)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP in the chain (original client)
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()
        
        # Fallback to direct connection IP
        return request.client.host if request.client else "unknown"

class HealthCheckMonitoring:
    """
    Health check and system monitoring utilities
    """
    
    def __init__(self):
        self.logger = get_logger("app.health")
    
    async def check_database_health(self, db_session) -> bool:
        """Check database connectivity"""
        try:
            # Simple query to test connection
            db_session.execute("SELECT 1")
            return True
        except Exception as e:
            self.logger.error(f"Database health check failed: {e}")
            return False
    
    async def check_redis_health(self, redis_client) -> bool:
        """Check Redis connectivity"""
        try:
            if redis_client:
                redis_client.ping()
                return True
            return False
        except Exception as e:
            self.logger.error(f"Redis health check failed: {e}")
            return False
    
    def get_system_metrics(self) -> dict:
        """Get basic system metrics"""
        import psutil
        
        try:
            return {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent,
                "load_average": psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else 0,
            }
        except Exception as e:
            self.logger.error(f"Failed to get system metrics: {e}")
            return {}

class MetricsCollector:
    """
    Simple metrics collection for monitoring
    """
    
    def __init__(self):
        self.metrics = {
            "requests_total": 0,
            "requests_by_status": {},
            "requests_by_endpoint": {},
            "response_times": [],
            "errors_total": 0,
        }
        self.logger = get_logger("app.metrics")
    
    def record_request(self, endpoint: str, method: str, status_code: int, duration_ms: float):
        """Record request metrics"""
        self.metrics["requests_total"] += 1
        
        # Track by status code
        status_key = f"{status_code}xx" if status_code >= 400 else "2xx"
        self.metrics["requests_by_status"][status_key] = \
            self.metrics["requests_by_status"].get(status_key, 0) + 1
        
        # Track by endpoint
        endpoint_key = f"{method} {endpoint}"
        self.metrics["requests_by_endpoint"][endpoint_key] = \
            self.metrics["requests_by_endpoint"].get(endpoint_key, 0) + 1
        
        # Track response times (keep only last 1000)
        self.metrics["response_times"].append(duration_ms)
        if len(self.metrics["response_times"]) > 1000:
            self.metrics["response_times"] = self.metrics["response_times"][-1000:]
        
        # Count errors
        if status_code >= 400:
            self.metrics["errors_total"] += 1
    
    def get_metrics_summary(self) -> dict:
        """Get metrics summary"""
        response_times = self.metrics["response_times"]
        
        summary = {
            "requests_total": self.metrics["requests_total"],
            "errors_total": self.metrics["errors_total"],
            "error_rate": (self.metrics["errors_total"] / max(1, self.metrics["requests_total"])) * 100,
            "requests_by_status": self.metrics["requests_by_status"],
            "top_endpoints": sorted(
                self.metrics["requests_by_endpoint"].items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
        }
        
        if response_times:
            response_times_sorted = sorted(response_times)
            summary.update({
                "avg_response_time": sum(response_times) / len(response_times),
                "median_response_time": response_times_sorted[len(response_times_sorted) // 2],
                "p95_response_time": response_times_sorted[int(len(response_times_sorted) * 0.95)],
                "p99_response_time": response_times_sorted[int(len(response_times_sorted) * 0.99)],
            })
        
        return summary
    
    def reset_metrics(self):
        """Reset all metrics"""
        self.__init__()

# Global instances
health_monitor = HealthCheckMonitoring()
metrics_collector = MetricsCollector()