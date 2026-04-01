"""
Redis Caching Layer Tests

Tests for Redis caching functionality including query result caching,
session management, and cache invalidation strategies.

Following TDD methodology: RED phase first.

@MX:SPEC: SPEC-PLATFORM-001 P2-T009
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
from typing import Any, Dict


class TestCacheManager:
    """Test cache manager functionality."""

    @pytest.mark.asyncio
    async def test_cache_manager_initialization(self):
        """Test cache manager initializes successfully."""
        from src.api.cache import CacheManager

        # Mock Redis client
        mock_redis = AsyncMock()

        # Create cache manager
        cache_manager = CacheManager(redis_client=mock_redis)

        assert cache_manager is not None
        assert cache_manager.redis == mock_redis

    @pytest.mark.asyncio
    async def test_set_with_ttl(self):
        """Test setting cache value with TTL."""
        from src.api.cache import CacheManager

        mock_redis = AsyncMock()
        cache_manager = CacheManager(redis_client=mock_redis)

        # Set value with 60 second TTL
        await cache_manager.set("test_key", {"data": "value"}, ttl=60)

        # Verify Redis SETEX was called
        mock_redis.setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_cached_value(self):
        """Test retrieving cached value."""
        from src.api.cache import CacheManager

        mock_redis = AsyncMock()
        mock_redis.get.return_value = b'{"data": "value"}'

        cache_manager = CacheManager(redis_client=mock_redis)

        # Get cached value
        value = await cache_manager.get("test_key")

        assert value is not None
        assert value["data"] == "value"

    @pytest.mark.asyncio
    async def test_get_missing_key(self):
        """Test retrieving non-existent key returns None."""
        from src.api.cache import CacheManager

        mock_redis = AsyncMock()
        mock_redis.get.return_value = None

        cache_manager = CacheManager(redis_client=mock_redis)

        # Get missing key
        value = await cache_manager.get("missing_key")

        assert value is None

    @pytest.mark.asyncio
    async def test_delete_cached_value(self):
        """Test deleting cached value."""
        from src.api.cache import CacheManager

        mock_redis = AsyncMock()
        mock_redis.delete.return_value = 1  # Return number of deleted keys

        cache_manager = CacheManager(redis_client=mock_redis)

        # Delete key
        result = await cache_manager.delete("test_key")

        # Verify Redis DEL was called
        mock_redis.delete.assert_called_once_with("test_key")
        assert result is True

    @pytest.mark.asyncio
    async def test_clear_pattern(self):
        """Test clearing keys by pattern."""
        from src.api.cache import CacheManager

        # Create a proper async iterator
        async def mock_scan_iter(match=None):
            """Mock async iterator for scan_iter."""
            for key in [b"key1", b"key2"]:
                yield key

        mock_redis = AsyncMock()
        # Wrap the mock_scan_iter to make it awaitable that returns an async iterator
        mock_redis.scan_iter = mock_scan_iter
        mock_redis.delete.return_value = 2

        cache_manager = CacheManager(redis_client=mock_redis)

        # Clear all keys matching pattern
        count = await cache_manager.clear_pattern("query:*")

        # Verify keys were deleted
        assert count == 2


class TestQueryResultCaching:
    """Test query result caching with TTL."""

    @pytest.mark.asyncio
    async def test_cache_query_result(self):
        """Test caching query results."""
        from src.api.cache import QueryCache

        mock_redis = AsyncMock()
        query_cache = QueryCache(redis_client=mock_redis)

        # Cache query result
        query = "SELECT * FROM users WHERE age > 18"
        result = {"rows": [{"id": 1, "name": "John"}], "row_count": 1}

        await query_cache.set(query, result, ttl=300)

        # Verify cache was set
        assert mock_redis.setex.called

    @pytest.mark.asyncio
    async def test_get_cached_query_result(self):
        """Test retrieving cached query result."""
        from src.api.cache import QueryCache

        mock_redis = AsyncMock()
        cached_data = b'{"rows": [{"id": 1}], "row_count": 1, "cached_at": "2024-01-01T00:00:00"}'
        mock_redis.get.return_value = cached_data

        query_cache = QueryCache(redis_client=mock_redis)

        # Get cached result
        query = "SELECT * FROM users WHERE age > 18"
        result = await query_cache.get(query)

        assert result is not None
        assert result["row_count"] == 1

    @pytest.mark.asyncio
    async def test_query_cache_key_generation(self):
        """Test cache key generation from query."""
        from src.api.cache import QueryCache

        query_cache = QueryCache(redis_client=AsyncMock())

        query = "SELECT * FROM users WHERE age > 18"
        cache_key = query_cache._generate_cache_key(query)

        assert "query:" in cache_key
        assert cache_key.startswith("query:")

    @pytest.mark.asyncio
    async def test_invalidate_query_cache_on_data_change(self):
        """Test cache invalidation when underlying data changes."""
        from src.api.cache import QueryCache

        # Create a proper async iterator
        async def mock_scan_iter(match=None):
            """Mock async iterator for scan_iter."""
            for key in [b"query:key1", b"query:key2"]:
                yield key

        mock_redis = AsyncMock()
        mock_redis.scan_iter = mock_scan_iter
        mock_redis.delete.return_value = 2

        query_cache = QueryCache(redis_client=mock_redis)

        # Invalidate cache for a table
        count = await query_cache.invalidate_table("users")

        # Verify cache keys were deleted
        assert count == 2


class TestSessionCaching:
    """Test session data caching."""

    @pytest.mark.asyncio
    async def test_store_session_data(self):
        """Test storing session data in cache."""
        from src.api.cache import SessionCache

        mock_redis = AsyncMock()
        session_cache = SessionCache(redis_client=mock_redis)

        # Store session data
        session_id = "sess_123"
        session_data = {
            "user_id": 1,
            "username": "testuser",
            "created_at": datetime.utcnow().isoformat()
        }

        await session_cache.set(session_id, session_data, ttl=3600)

        # Verify session was cached
        assert mock_redis.setex.called

    @pytest.mark.asyncio
    async def test_retrieve_session_data(self):
        """Test retrieving session data from cache."""
        from src.api.cache import SessionCache

        mock_redis = AsyncMock()
        session_data = b'{"user_id": 1, "username": "testuser"}'
        mock_redis.get.return_value = session_data

        session_cache = SessionCache(redis_client=mock_redis)

        # Get session
        session = await session_cache.get("sess_123")

        assert session is not None
        assert session["user_id"] == 1

    @pytest.mark.asyncio
    async def test_session_expiration(self):
        """Test session expires after TTL."""
        from src.api.cache import SessionCache

        mock_redis = AsyncMock()
        mock_redis.get.return_value = None  # Expired

        session_cache = SessionCache(redis_client=mock_redis)

        # Try to get expired session
        session = await session_cache.get("sess_123")

        assert session is None


class TestCacheMetrics:
    """Test cache hit/miss metrics."""

    @pytest.mark.asyncio
    async def test_record_cache_hit(self):
        """Test recording cache hit."""
        from src.api.cache import CacheMetrics

        mock_redis = AsyncMock()
        metrics = CacheMetrics(redis_client=mock_redis)

        # Record hit
        await metrics.record_hit("query_cache")

        # Verify counter incremented
        assert mock_redis.incr.called

    @pytest.mark.asyncio
    async def test_record_cache_miss(self):
        """Test recording cache miss."""
        from src.api.cache import CacheMetrics

        mock_redis = AsyncMock()
        metrics = CacheMetrics(redis_client=mock_redis)

        # Record miss
        await metrics.record_miss("query_cache")

        # Verify counter incremented
        assert mock_redis.incr.called

    @pytest.mark.asyncio
    async def test_get_cache_stats(self):
        """Test retrieving cache statistics."""
        from src.api.cache import CacheMetrics

        mock_redis = AsyncMock()
        # Mock mget to return [hits, misses]
        mock_redis.mget.return_value = [b"100", b"10"]  # 100 hits, 10 misses

        metrics = CacheMetrics(redis_client=mock_redis)

        # Get stats
        stats = await metrics.get_stats("query_cache")

        assert stats["hits"] == 100
        assert stats["misses"] == 10
        assert stats["hit_rate"] == pytest.approx(0.9091, rel=1e-3)  # 100/110 ≈ 0.9091

    @pytest.mark.asyncio
    async def test_reset_metrics(self):
        """Test resetting cache metrics."""
        from src.api.cache import CacheMetrics

        mock_redis = AsyncMock()
        metrics = CacheMetrics(redis_client=mock_redis)

        # Reset metrics
        await metrics.reset("query_cache")

        # Verify keys were deleted
        assert mock_redis.delete.called


class TestCacheInvalidationStrategies:
    """Test cache invalidation strategies."""

    @pytest.mark.asyncio
    async def test_time_based_invalidation(self):
        """Test time-based cache invalidation."""
        from src.api.cache.strategies import TimeBasedInvalidation

        strategy = TimeBasedInvalidation(ttl=300)

        # Check if cache entry is expired
        cached_at = datetime.utcnow() - timedelta(seconds=400)
        is_expired = strategy.is_expired(cached_at)

        assert is_expired is True

    @pytest.mark.asyncio
    async def test_event_based_invalidation(self):
        """Test event-based cache invalidation."""
        from src.api.cache.strategies import EventBasedInvalidation

        # Create a proper async iterator
        async def mock_scan_iter(match=None):
            """Mock async iterator for scan_iter."""
            for key in [b"query:select1", b"query:select2"]:
                yield key

        mock_redis = AsyncMock()
        mock_redis.scan_iter = mock_scan_iter
        mock_redis.delete.return_value = 2

        strategy = EventBasedInvalidation(redis_client=mock_redis)

        # Trigger invalidation event
        count = await strategy.invalidate_on_write("users", "INSERT")

        # Verify related cache keys were cleared
        assert count == 2
        assert mock_redis.delete.called

    @pytest.mark.asyncio
    async def test_tag_based_invalidation(self):
        """Test tag-based cache invalidation."""
        from src.api.cache.strategies import TagBasedInvalidation

        mock_redis = AsyncMock()
        mock_redis.smembers.return_value = {b"key1", b"key2", b"key3"}
        strategy = TagBasedInvalidation(redis_client=mock_redis)

        # Invalidate by tag
        await strategy.invalidate_by_tag("user_data")

        # Verify all keys with tag were deleted
        assert mock_redis.delete.called
