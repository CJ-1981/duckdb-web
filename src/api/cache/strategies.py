"""
Cache Invalidation Strategies

Multiple strategies for cache invalidation:
- Time-based: TTL expiration
- Event-based: Invalidate on data changes
- Tag-based: Group related cache entries

@MX:SPEC: SPEC-PLATFORM-001 P2-T009
"""

from typing import Any, Set
from datetime import datetime, timedelta


class TimeBasedInvalidation:
    """
    Time-based cache invalidation using TTL.

    Simplest strategy - entries expire after fixed time period.

    Attributes:
        ttl: Time to live in seconds

    @MX:NOTE: Default strategy for most cache entries
    """

    def __init__(self, ttl: int = 300):
        """
        Initialize time-based invalidation.

        Args:
            ttl: Default TTL in seconds (default: 5 minutes)
        """
        self.ttl = ttl

    def is_expired(self, cached_at: datetime) -> bool:
        """
        Check if cache entry is expired.

        Args:
            cached_at: When the entry was cached

        Returns:
            True if expired, False otherwise
        """
        age = datetime.utcnow() - cached_at
        return age.total_seconds() > self.ttl

    def get_ttl(self) -> int:
        """
        Get the TTL value.

        Returns:
            TTL in seconds
        """
        return self.ttl


class EventBasedInvalidation:
    """
    Event-based cache invalidation.

    Invalidates cache entries when specific events occur
    (e.g., database writes, schema changes).

    Attributes:
        redis: Redis client for cache operations

    @MX:NOTE: Most precise invalidation but requires event hooks
    """

    def __init__(self, redis_client: Any):
        """
        Initialize event-based invalidation.

        Args:
            redis_client: Redis client instance
        """
        self.redis = redis_client

    async def invalidate_on_write(self, table_name: str, operation: str) -> int:
        """
        Invalidate cache entries affected by a write operation.

        Args:
            table_name: Table that was modified
            operation: Type of operation (INSERT, UPDATE, DELETE)

        Returns:
            Number of cache keys invalidated

        @MX:ANCHOR: Write-based invalidation entry point (fan_in >= 3: all write operations)
        """
        # Clear all query cache entries
        # In production, use table->query mapping
        pattern = "query:*"

        keys = []
        async for key in self.redis.scan_iter(match=pattern):
            keys.append(key)

        if keys:
            return await self.redis.delete(*keys)

        return 0

    async def invalidate_on_schema_change(self, schema_name: str) -> int:
        """
        Invalidate cache entries on schema changes.

        Args:
            schema_name: Schema that was modified

        Returns:
            Number of cache keys invalidated
        """
        # Clear all caches for safety
        pattern = "*"

        keys = []
        async for key in self.redis.scan_iter(match=pattern):
            # Only clear query and data caches
            key_str = key.decode()
            if key_str.startswith("query:") or key_str.startswith("data:"):
                keys.append(key)

        if keys:
            return await self.redis.delete(*keys)

        return 0


class TagBasedInvalidation:
    """
    Tag-based cache invalidation.

    Groups related cache entries by tags and invalidates
    entire groups at once.

    Attributes:
        redis: Redis client for cache operations

    @MX:NOTE: Useful for invalidating related entities (e.g., user + user's workflows)
    """

    def __init__(self, redis_client: Any):
        """
        Initialize tag-based invalidation.

        Args:
            redis_client: Redis client instance
        """
        self.redis = redis_client

    async def add_tag(self, cache_key: str, tag: str) -> None:
        """
        Add a tag to a cache entry.

        Args:
            cache_key: Cache entry key
            tag: Tag to add
        """
        tag_key = self._generate_tag_key(tag)
        await self.redis.sadd(tag_key, cache_key)

    async def invalidate_by_tag(self, tag: str) -> int:
        """
        Invalidate all cache entries with a tag.

        Args:
            tag: Tag to invalidate

        Returns:
            Number of cache keys invalidated

        @MX:ANCHOR: Tag-based invalidation entry point (fan_in >= 3: bulk operations, cascading deletes)
        """
        tag_key = self._generate_tag_key(tag)

        # Get all keys with this tag
        members = await self.redis.smembers(tag_key)

        if members:
            # Convert bytes to strings if needed
            keys = [m.decode() if isinstance(m, bytes) else m for m in members]

            # Delete all tagged keys
            result = await self.redis.delete(*keys)

            # Clear the tag set
            await self.redis.delete(tag_key)

            return result

        return 0

    async def remove_tag(self, cache_key: str, tag: str) -> None:
        """
        Remove a tag from a cache entry.

        Args:
            cache_key: Cache entry key
            tag: Tag to remove
        """
        tag_key = self._generate_tag_key(tag)
        await self.redis.srem(tag_key, cache_key)

    def _generate_tag_key(self, tag: str) -> str:
        """
        Generate Redis key for a tag.

        Args:
            tag: Tag name

        Returns:
            Tag key
        """
        return f"tag:{tag}"


class HybridInvalidation:
    """
    Hybrid invalidation combining multiple strategies.

    Uses time-based as fallback with event-based for precision.

    Attributes:
        time_based: Time-based strategy
        event_based: Event-based strategy
        tag_based: Tag-based strategy

    @MX:NOTE: Most flexible approach for production use
    """

    def __init__(self, redis_client: Any, default_ttl: int = 300):
        """
        Initialize hybrid invalidation.

        Args:
            redis_client: Redis client instance
            default_ttl: Default TTL for time-based strategy
        """
        self.time_based = TimeBasedInvalidation(ttl=default_ttl)
        self.event_based = EventBasedInvalidation(redis_client)
        self.tag_based = TagBasedInvalidation(redis_client)

    async def invalidate_on_write(self, table_name: str, operation: str) -> int:
        """Invalidate using event-based strategy."""
        return await self.event_based.invalidate_on_write(table_name, operation)

    async def invalidate_by_tag(self, tag: str) -> int:
        """Invalidate using tag-based strategy."""
        return await self.tag_based.invalidate_by_tag(tag)

    def is_expired(self, cached_at: datetime) -> bool:
        """Check expiration using time-based strategy."""
        return self.time_based.is_expired(cached_at)


__all__ = [
    'TimeBasedInvalidation',
    'EventBasedInvalidation',
    'TagBasedInvalidation',
    'HybridInvalidation'
]
