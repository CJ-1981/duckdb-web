"""
Cache Metrics

Cache performance tracking with hit/miss statistics.
Provides insights into cache effectiveness.

@MX:SPEC: SPEC-PLATFORM-001 P2-T009
"""

from typing import Dict, Any
from .manager import CacheManager


class CacheMetrics:
    """
    Cache performance metrics tracking.

    Tracks hit rates, miss counts, and provides statistics
    for monitoring cache effectiveness.

    Attributes:
        redis: Redis client
        manager: Cache manager instance

    @MX:NOTE: Metrics stored in Redis for persistence and distributed tracking
    """

    def __init__(self, redis_client: Any):
        """
        Initialize cache metrics tracker.

        Args:
            redis_client: Redis client instance
        """
        self.redis = redis_client
        self.manager = CacheManager(redis_client)

    async def record_hit(self, cache_name: str) -> None:
        """
        Record a cache hit.

        Args:
            cache_name: Name of the cache (e.g., "query_cache", "session_cache")

        @MX:ANCHOR: Hit recording entry point (fan_in >= 3: QueryCache, SessionCache, direct usage)
        """
        hit_key = self._generate_key("hits", cache_name)
        await self.redis.incr(hit_key)

    async def record_miss(self, cache_name: str) -> None:
        """
        Record a cache miss.

        Args:
            cache_name: Name of the cache
        """
        miss_key = self._generate_key("misses", cache_name)
        await self.redis.incr(miss_key)

    async def get_stats(self, cache_name: str) -> Dict[str, Any]:
        """
        Get cache statistics.

        Args:
            cache_name: Name of the cache

        Returns:
            Dictionary with hits, misses, and hit_rate
        """
        hit_key = self._generate_key("hits", cache_name)
        miss_key = self._generate_key("misses", cache_name)

        # Get counters
        values = await self.redis.mget(hit_key, miss_key)

        hits = int(values[0] or 0)
        misses = int(values[1] or 0)
        total = hits + misses

        # Calculate hit rate
        hit_rate = hits / total if total > 0 else 0.0

        return {
            "cache_name": cache_name,
            "hits": hits,
            "misses": misses,
            "total_requests": total,
            "hit_rate": round(hit_rate, 4)
        }

    async def reset(self, cache_name: str) -> None:
        """
        Reset metrics for a cache.

        Args:
            cache_name: Name of the cache to reset
        """
        hit_key = self._generate_key("hits", cache_name)
        miss_key = self._generate_key("misses", cache_name)

        await self.redis.delete(hit_key, miss_key)

    async def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """
        Get statistics for all tracked caches.

        Returns:
            Dictionary mapping cache names to their stats

        @MX:TODO: Auto-discover cache names from metrics keys
        """
        # Known cache names
        cache_names = ["query_cache", "session_cache"]

        stats = {}
        for name in cache_names:
            stats[name] = await self.get_stats(name)

        return stats

    def _generate_key(self, metric_type: str, cache_name: str) -> str:
        """
        Generate Redis key for metric.

        Args:
            metric_type: Type of metric ("hits" or "misses")
            cache_name: Name of the cache

        Returns:
            Metric key
        """
        return self.manager.generate_key("metrics", metric_type, cache_name)


__all__ = ['CacheMetrics']
