"""
ABOUTME: Redis caching service for performance optimization.
ABOUTME: Provides async caching with TTL, decorators, and cache invalidation.
"""

import json
import pickle
from typing import Optional, Any, Callable
from datetime import timedelta
from functools import wraps
import hashlib
import logging

import redis.asyncio as redis

from config.settings import settings

logger = logging.getLogger(__name__)


class CacheService:
    """Async Redis cache service."""

    def __init__(self):
        self._client: Optional[redis.Redis] = None

    async def connect(self):
        """Connect to Redis."""
        try:
            self._client = redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=False,  # Handle binary data
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Test connection
            await self._client.ping()
            logger.info(f"Connected to Redis at {settings.redis_url}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self._client = None

    async def close(self):
        """Close Redis connection."""
        if self._client:
            await self._client.close()
            logger.info("Redis connection closed")

    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        if not self._client:
            return None

        try:
            value = await self._client.get(key)
            if value:
                return pickle.loads(value)
        except Exception as e:
            logger.warning(f"Cache get error for key '{key}': {e}")

        return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int = 300  # 5 minutes default
    ):
        """
        Set value in cache with TTL.

        Args:
            key: Cache key
            value: Value to cache (must be picklable)
            ttl: Time to live in seconds
        """
        if not self._client:
            return

        try:
            await self._client.set(
                key,
                pickle.dumps(value),
                ex=ttl
            )
        except Exception as e:
            logger.warning(f"Cache set error for key '{key}': {e}")

    async def delete(self, key: str):
        """
        Delete value from cache.

        Args:
            key: Cache key
        """
        if not self._client:
            return

        try:
            await self._client.delete(key)
        except Exception as e:
            logger.warning(f"Cache delete error for key '{key}': {e}")

    async def delete_pattern(self, pattern: str):
        """
        Delete all keys matching pattern.

        Args:
            pattern: Key pattern (e.g., "agent:*")
        """
        if not self._client:
            return

        try:
            keys = await self._client.keys(pattern)
            if keys:
                await self._client.delete(*keys)
                logger.info(f"Deleted {len(keys)} keys matching '{pattern}'")
        except Exception as e:
            logger.warning(f"Cache delete pattern error for '{pattern}': {e}")

    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if key exists
        """
        if not self._client:
            return False

        try:
            return await self._client.exists(key) > 0
        except Exception as e:
            logger.warning(f"Cache exists error for key '{key}': {e}")
            return False

    async def ttl(self, key: str) -> int:
        """
        Get remaining TTL for key.

        Args:
            key: Cache key

        Returns:
            Remaining seconds, -1 if no expiry, -2 if key doesn't exist
        """
        if not self._client:
            return -2

        try:
            return await self._client.ttl(key)
        except Exception as e:
            logger.warning(f"Cache TTL error for key '{key}': {e}")
            return -2

    @staticmethod
    def generate_key(*args, prefix: str = "cache", **kwargs) -> str:
        """
        Generate cache key from arguments.

        Args:
            *args: Positional arguments
            prefix: Key prefix
            **kwargs: Keyword arguments

        Returns:
            Cache key string
        """
        # Create deterministic key from arguments
        parts = [str(arg) for arg in args]
        parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
        key_data = ":".join(parts)

        # Hash long keys
        if len(key_data) > 100:
            key_hash = hashlib.md5(key_data.encode()).hexdigest()
            return f"{prefix}:{key_hash}"

        return f"{prefix}:{key_data}"


# Global cache instance
cache_service = CacheService()


def cached(ttl: int = 300, prefix: str = "cache"):
    """
    Decorator to cache function results.

    Args:
        ttl: Cache TTL in seconds
        prefix: Cache key prefix

    Example:
        @cached(ttl=600, prefix="agent")
        async def get_agent(agent_id: str):
            return await db.get(Agent, agent_id)
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            key = CacheService.generate_key(*args, prefix=f"{prefix}:{func.__name__}", **kwargs)

            # Try to get from cache
            cached_value = await cache_service.get(key)
            if cached_value is not None:
                logger.debug(f"Cache hit for {key}")
                return cached_value

            # Call function
            result = await func(*args, **kwargs)

            # Cache result
            await cache_service.set(key, result, ttl=ttl)
            logger.debug(f"Cache miss for {key}, cached for {ttl}s")

            return result

        return wrapper
    return decorator


async def get_cache_service() -> CacheService:
    """Get cache service instance."""
    return cache_service

