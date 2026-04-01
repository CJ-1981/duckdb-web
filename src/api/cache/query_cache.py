"""
Query Cache

Caching layer for DuckDB query results with intelligent
invalidation strategies.

@MX:SPEC: SPEC-PLATFORM-001 P2-T009
"""

from typing import Any, Optional, Dict
from datetime import datetime
from .manager import CacheManager


class QueryCache:
    """
    Query result cache with automatic invalidation.

    Provides caching for DuckDB query results with table-aware
    invalidation strategies.

    Attributes:
        redis: Redis client
        manager: Cache manager instance
        default_ttl: Default TTL for query results (300 seconds)

    @MX:NOTE: Query results cached to reduce redundant DuckDB executions
    """

    def __init__(self, redis_client: Any, default_ttl: int = 300):
        """
        Initialize query cache.

        Args:
            redis_client: Redis client instance
            default_ttl: Default TTL in seconds (default: 5 minutes)
        """
        self.redis = redis_client
        self.manager = CacheManager(redis_client)
        self.default_ttl = default_ttl

    async def set(self, query: str, result: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """
        Cache a query result.

        Args:
            query: SQL query string
            result: Query result (rows, row_count, metadata)
            ttl: Override default TTL

        Returns:
            True if cached successfully
        """
        # Add cache timestamp
        result["cached_at"] = datetime.utcnow().isoformat()

        # Generate cache key
        cache_key = self._generate_cache_key(query)

        # Set with TTL
        ttl = ttl or self.default_ttl
        return await self.manager.set(cache_key, result, ttl=ttl)

    async def get(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Get cached query result.

        Args:
            query: SQL query string

        Returns:
            Cached result or None if not found/expired
        """
        cache_key = self._generate_cache_key(query)
        return await self.manager.get(cache_key)

    async def invalidate_table(self, table_name: str) -> int:
        """
        Invalidate all cached queries for a specific table.

        Args:
            table_name: Name of the table that was modified

        Returns:
            Number of cache keys invalidated

        @MX:ANCHOR: Table-based invalidation entry point (fan_in >= 3: write operations, schema changes, manual invalidation)
        """
        # Clear all query cache keys (simplified approach)
        # In production, maintain table->query mapping
        pattern = "query:*"
        return await self.manager.clear_pattern(pattern)

    def _generate_cache_key(self, query: str) -> str:
        """
        Generate a consistent cache key for a query.

        Args:
            query: SQL query string

        Returns:
            Cache key with "query:" prefix

        @MX:NOTE: Normalizes query (whitespace, case) before hashing
        """
        # Normalize query
        normalized = " ".join(query.strip().split())

        # Hash if query is very long
        if len(normalized) > 100:
            normalized = self.manager.hash_key(normalized)

        # Generate key
        return self.manager.generate_key("query", normalized)

    async def get_stats(self) -> Dict[str, int]:
        """
        Get query cache statistics.

        Returns:
            Dictionary with cache statistics

        @MX:TODO: Implement per-query stats tracking
        """
        # Count query cache keys
        pattern = "query:*"
        keys = []
        async for key in self.redis.scan_iter(match=pattern):
            keys.append(key)

        return {
            "total_cached_queries": len(keys),
            "default_ttl": self.default_ttl
        }


__all__ = ['QueryCache']
