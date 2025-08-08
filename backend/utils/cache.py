"""
Redis caching utilities for improved performance
"""
import json
import pickle
from typing import Any, Optional, Union, List, Dict, Callable
from datetime import datetime, timedelta
import hashlib
import logging
from functools import wraps
import asyncio

try:
    import redis
    import aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from pydantic_settings import BaseSettings

logger = logging.getLogger("app.cache")

class CacheSettings(BaseSettings):
    redis_url: str = "redis://localhost:6379"
    redis_password: Optional[str] = None
    redis_db: int = 0
    cache_default_ttl: int = 300  # 5 minutes default TTL
    cache_prefix: str = "fastapi_ecommerce"
    
    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        extra = 'ignore'

settings = CacheSettings()

class CacheManager:
    """
    Centralized cache manager with Redis backend and in-memory fallback
    """
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.async_redis_client: Optional[aioredis.Redis] = None
        self.in_memory_cache: Dict[str, Dict] = {}
        self.cache_hits = 0
        self.cache_misses = 0
        self._setup_redis()
    
    def _setup_redis(self):
        """Initialize Redis connections"""
        if not REDIS_AVAILABLE:
            logger.warning("Redis not available, using in-memory cache fallback")
            return
        
        try:
            # Synchronous Redis client
            self.redis_client = redis.from_url(
                settings.redis_url,
                password=settings.redis_password,
                db=settings.redis_db,
                decode_responses=False,  # We'll handle encoding ourselves
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # Test connection
            self.redis_client.ping()
            logger.info("Redis connection established successfully")
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis_client = None
    
    async def setup_async_redis(self):
        """Initialize async Redis connection"""
        if not REDIS_AVAILABLE or not self.redis_client:
            return
        
        try:
            self.async_redis_client = aioredis.from_url(
                settings.redis_url,
                password=settings.redis_password,
                db=settings.redis_db,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
            )
            
            # Test connection
            await self.async_redis_client.ping()
            logger.info("Async Redis connection established successfully")
            
        except Exception as e:
            logger.error(f"Failed to setup async Redis: {e}")
            self.async_redis_client = None
    
    def _get_cache_key(self, key: str) -> str:
        """Generate full cache key with prefix"""
        return f"{settings.cache_prefix}:{key}"
    
    def _serialize_value(self, value: Any) -> bytes:
        """Serialize value for storage"""
        try:
            # Try JSON first for simple types
            if isinstance(value, (str, int, float, bool, list, dict, type(None))):
                return json.dumps(value).encode('utf-8')
            else:
                # Use pickle for complex objects
                return pickle.dumps(value)
        except Exception as e:
            logger.error(f"Failed to serialize value: {e}")
            return pickle.dumps(value)
    
    def _deserialize_value(self, data: bytes) -> Any:
        """Deserialize value from storage"""
        try:
            # Try JSON first
            return json.loads(data.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            # Fallback to pickle
            return pickle.loads(data)
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set a value in cache"""
        cache_key = self._get_cache_key(key)
        ttl = ttl or settings.cache_default_ttl
        
        if self.redis_client:
            try:
                serialized_value = self._serialize_value(value)
                result = self.redis_client.setex(cache_key, ttl, serialized_value)
                logger.debug(f"Cache SET: {key} (TTL: {ttl}s)")
                return result
            except Exception as e:
                logger.error(f"Redis SET failed for {key}: {e}")
        
        # Fallback to in-memory cache
        expiry = datetime.now() + timedelta(seconds=ttl)
        self.in_memory_cache[cache_key] = {
            'value': value,
            'expiry': expiry
        }
        logger.debug(f"In-memory cache SET: {key}")
        return True
    
    def get(self, key: str) -> Optional[Any]:
        """Get a value from cache"""
        cache_key = self._get_cache_key(key)
        
        if self.redis_client:
            try:
                data = self.redis_client.get(cache_key)
                if data is not None:
                    self.cache_hits += 1
                    logger.debug(f"Cache HIT: {key}")
                    return self._deserialize_value(data)
                else:
                    self.cache_misses += 1
                    logger.debug(f"Cache MISS: {key}")
                    return None
            except Exception as e:
                logger.error(f"Redis GET failed for {key}: {e}")
        
        # Fallback to in-memory cache
        if cache_key in self.in_memory_cache:
            cache_entry = self.in_memory_cache[cache_key]
            if datetime.now() < cache_entry['expiry']:
                self.cache_hits += 1
                logger.debug(f"In-memory cache HIT: {key}")
                return cache_entry['value']
            else:
                # Expired entry
                del self.in_memory_cache[cache_key]
        
        self.cache_misses += 1
        logger.debug(f"Cache MISS: {key}")
        return None
    
    async def aset(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Async set a value in cache"""
        if not self.async_redis_client:
            await self.setup_async_redis()
        
        cache_key = self._get_cache_key(key)
        ttl = ttl or settings.cache_default_ttl
        
        if self.async_redis_client:
            try:
                serialized_value = self._serialize_value(value)
                await self.async_redis_client.setex(cache_key, ttl, serialized_value)
                logger.debug(f"Async cache SET: {key} (TTL: {ttl}s)")
                return True
            except Exception as e:
                logger.error(f"Async Redis SET failed for {key}: {e}")
        
        # Fallback to sync method
        return self.set(key, value, ttl)
    
    async def aget(self, key: str) -> Optional[Any]:
        """Async get a value from cache"""
        if not self.async_redis_client:
            await self.setup_async_redis()
        
        cache_key = self._get_cache_key(key)
        
        if self.async_redis_client:
            try:
                data = await self.async_redis_client.get(cache_key)
                if data is not None:
                    self.cache_hits += 1
                    logger.debug(f"Async cache HIT: {key}")
                    return self._deserialize_value(data)
                else:
                    self.cache_misses += 1
                    logger.debug(f"Async cache MISS: {key}")
                    return None
            except Exception as e:
                logger.error(f"Async Redis GET failed for {key}: {e}")
        
        # Fallback to sync method
        return self.get(key)
    
    def delete(self, key: str) -> bool:
        """Delete a value from cache"""
        cache_key = self._get_cache_key(key)
        
        if self.redis_client:
            try:
                result = self.redis_client.delete(cache_key)
                logger.debug(f"Cache DELETE: {key}")
                return bool(result)
            except Exception as e:
                logger.error(f"Redis DELETE failed for {key}: {e}")
        
        # Fallback to in-memory cache
        if cache_key in self.in_memory_cache:
            del self.in_memory_cache[cache_key]
            logger.debug(f"In-memory cache DELETE: {key}")
            return True
        
        return False
    
    def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching a pattern"""
        full_pattern = self._get_cache_key(pattern)
        
        if self.redis_client:
            try:
                keys = self.redis_client.keys(full_pattern)
                if keys:
                    count = self.redis_client.delete(*keys)
                    logger.debug(f"Cache DELETE PATTERN: {pattern} ({count} keys)")
                    return count
                return 0
            except Exception as e:
                logger.error(f"Redis DELETE PATTERN failed for {pattern}: {e}")
        
        # Fallback to in-memory cache
        count = 0
        keys_to_delete = []
        for key in self.in_memory_cache.keys():
            if pattern.replace('*', '') in key:
                keys_to_delete.append(key)
        
        for key in keys_to_delete:
            del self.in_memory_cache[key]
            count += 1
        
        logger.debug(f"In-memory cache DELETE PATTERN: {pattern} ({count} keys)")
        return count
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total_requests * 100) if total_requests > 0 else 0
        
        stats = {
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "hit_rate_percentage": round(hit_rate, 2),
            "using_redis": self.redis_client is not None,
            "in_memory_keys": len(self.in_memory_cache)
        }
        
        if self.redis_client:
            try:
                info = self.redis_client.info()
                stats.update({
                    "redis_memory_used": info.get("used_memory_human", "N/A"),
                    "redis_connected_clients": info.get("connected_clients", 0),
                    "redis_keys": info.get("db0", {}).get("keys", 0) if "db0" in info else 0
                })
            except Exception as e:
                logger.error(f"Failed to get Redis stats: {e}")
        
        return stats
    
    def clear_all(self) -> bool:
        """Clear all cached data"""
        if self.redis_client:
            try:
                pattern = self._get_cache_key("*")
                keys = self.redis_client.keys(pattern)
                if keys:
                    self.redis_client.delete(*keys)
                logger.info("Redis cache cleared")
                return True
            except Exception as e:
                logger.error(f"Failed to clear Redis cache: {e}")
        
        # Clear in-memory cache
        self.in_memory_cache.clear()
        logger.info("In-memory cache cleared")
        return True

# Global cache manager instance
cache_manager = CacheManager()

# Convenience functions
def cache_set(key: str, value: Any, ttl: Optional[int] = None) -> bool:
    """Set a value in cache"""
    return cache_manager.set(key, value, ttl)

def cache_get(key: str) -> Optional[Any]:
    """Get a value from cache"""
    return cache_manager.get(key)

def cache_delete(key: str) -> bool:
    """Delete a value from cache"""
    return cache_manager.delete(key)

async def async_cache_set(key: str, value: Any, ttl: Optional[int] = None) -> bool:
    """Async set a value in cache"""
    return await cache_manager.aset(key, value, ttl)

async def async_cache_get(key: str) -> Optional[Any]:
    """Async get a value from cache"""
    return await cache_manager.aget(key)

# Decorators for caching
def cached(ttl: Optional[int] = None, key_func: Optional[Callable] = None):
    """
    Decorator to cache function results
    
    Args:
        ttl: Time to live in seconds
        key_func: Function to generate cache key from arguments
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Create key from function name and arguments
                arg_str = str(args) + str(sorted(kwargs.items()))
                cache_key = f"{func.__name__}:{hashlib.md5(arg_str.encode()).hexdigest()}"
            
            # Try to get from cache
            cached_result = cache_get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_set(cache_key, result, ttl)
            return result
        
        return wrapper
    return decorator

def async_cached(ttl: Optional[int] = None, key_func: Optional[Callable] = None):
    """
    Async decorator to cache function results
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Create key from function name and arguments
                arg_str = str(args) + str(sorted(kwargs.items()))
                cache_key = f"{func.__name__}:{hashlib.md5(arg_str.encode()).hexdigest()}"
            
            # Try to get from cache
            cached_result = await async_cache_get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            await async_cache_set(cache_key, result, ttl)
            return result
        
        return wrapper
    return decorator

# Cache invalidation helpers
class CacheInvalidator:
    """Helper class for cache invalidation patterns"""
    
    @staticmethod
    def invalidate_user_cache(user_id: int):
        """Invalidate all cache entries for a specific user"""
        patterns = [
            f"user:{user_id}:*",
            f"cart:user:{user_id}:*",
            f"purchases:user:{user_id}:*"
        ]
        
        for pattern in patterns:
            cache_manager.delete_pattern(pattern)
    
    @staticmethod
    def invalidate_item_cache(item_id: int):
        """Invalidate all cache entries for a specific item"""
        patterns = [
            f"item:{item_id}:*",
            f"items:*",  # Invalidate item lists
            "categories:*"
        ]
        
        for pattern in patterns:
            cache_manager.delete_pattern(pattern)
    
    @staticmethod
    def invalidate_category_cache(category: str):
        """Invalidate cache entries for a specific category"""
        patterns = [
            f"category:{category}:*",
            f"items:category:{category}:*",
            "categories:*"
        ]
        
        for pattern in patterns:
            cache_manager.delete_pattern(pattern)

# Export invalidator instance
cache_invalidator = CacheInvalidator()