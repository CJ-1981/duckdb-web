"""
Cache Manager

Core cache manager with Redis client integration.
Provides basic get/set/delete operations with TTL support.

@MX:SPEC: SPEC-PLATFORM-001 P2-T009
"""

import json
import hashlib
from typing import Any, Optional
from datetime import datetime


class CacheManager:
    """
    Core cache manager for Redis operations.

    Provides thread-safe caching operations with TTL support.

    Attributes:
        redis: Redis client instance

    @MX:ANCHOR: Cache manager core (fan_in >= 3: QueryCache, SessionCache, direct usage)
    """

    def __init__(self, redis_client: Any):
        """
        Initialize cache manager.

        Args:
            redis_client: Redis client (aioredis or redis-py async)
        """
        self.redis = redis_client

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set a cache value with optional TTL.

        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Time to live in seconds

        Returns:
            True if set successfully, False otherwise

        @MX:NOTE: Values are JSON serialized for storage
        """
        # Serialize value to JSON
        serialized = json.dumps(value)

        # Set with TTL if specified
        if ttl:
            await self.redis.setex(key, ttl, serialized)
        else:
            await self.redis.set(key, serialized)

        return True

    async def get(self, key: str) -> Optional[Any]:
        """
        Get a cached value.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        # Get from Redis
        value = await self.redis.get(key)

        if value is None:
            return None

        # Deserialize JSON
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            # Return raw value if not JSON
            return value

    async def delete(self, key: str) -> bool:
        """
        Delete a cached value.

        Args:
            key: Cache key

        Returns:
            True if deleted, False otherwise
        """
        result = await self.redis.delete(key)
        return result > 0

    async def exists(self, key: str) -> bool:
        """
        Check if a key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if key exists, False otherwise
        """
        result = await self.redis.exists(key)
        return result > 0

    async def clear_pattern(self, pattern: str) -> int:
        """
        Clear all keys matching a pattern.

        Args:
            pattern: Key pattern (e.g., "query:*", "session:*")

        Returns:
            Number of keys deleted

        @MX:NOTE: Uses SCAN for production safety (avoids blocking)
        """
        keys = []
        async for key in self.redis.scan_iter(match=pattern):
            keys.append(key)

        if keys:
            return await self.redis.delete(*keys)

        return 0

    def generate_key(self, *parts: str) -> str:
        """
        Generate a cache key from parts.

        Args:
            *parts: Key parts to join

        Returns:
            Colon-separated cache key
        """
        return ":".join(str(part) for part in parts)

    def hash_key(self, data: str) -> str:
        """
        Generate a hash of data for cache keys.

        Args:
            data: Data to hash

        Returns:
            SHA256 hash as hex string

        @MX:NOTE: Used for long query strings or complex keys
        """
        return hashlib.sha256(data.encode()).hexdigest()


__all__ = ['CacheManager']
