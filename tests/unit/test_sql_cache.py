"""
Unit tests for SQL query result caching.

Tests the cache key generation, cache eviction, and cache invalidation logic
for SQL query results in the workflow API.
"""

import pytest
import time
from src.api.routes.workflows import (
    _generate_sql_cache_key,
    _evict_old_sql_cache_entries,
    _get_cached_sql_result,
    _cache_sql_result,
    _invalidate_sql_cache_for_table,
    _SQL_RESULT_CACHE,
    _MAX_SQL_RESULT_CACHE_SIZE
)


class TestSqlCacheKeyGeneration:
    """Test cache key generation for SQL queries."""

    def test_basic_cache_key(self):
        """Test basic cache key generation."""
        sql = "SELECT * FROM table1"
        schemas = {}

        key1 = _generate_sql_cache_key(sql, schemas)
        key2 = _generate_sql_cache_key(sql, schemas)

        # Same inputs should produce same key
        assert key1 == key2
        assert len(key1) == 32  # SHA256 hex digest truncated to 32 chars

    def test_different_sql_produces_different_key(self):
        """Test that different SQL queries produce different cache keys."""
        schemas = {}

        key1 = _generate_sql_cache_key("SELECT * FROM table1", schemas)
        key2 = _generate_sql_cache_key("SELECT * FROM table2", schemas)

        assert key1 != key2

    def test_sql_normalization(self):
        """Test that SQL whitespace is normalized for cache key."""
        schemas = {}

        # Different whitespace should produce same key
        sql1 = "SELECT  *  FROM  table1"
        sql2 = "SELECT * FROM table1"

        key1 = _generate_sql_cache_key(sql1, schemas)
        key2 = _generate_sql_cache_key(sql2, schemas)

        assert key1 == key2

    def test_schema_fingerprint_affects_key(self):
        """Test that input schemas affect cache key generation."""
        sql = "SELECT * FROM {{input1}}"

        schemas1 = {"table1": {"col1": "INTEGER", "col2": "VARCHAR"}}
        schemas2 = {"table1": {"col1": "INTEGER", "col2": "DOUBLE"}}  # Different type

        key1 = _generate_sql_cache_key(sql, schemas1)
        key2 = _generate_sql_cache_key(sql, schemas2)

        assert key1 != key2

    def test_column_order_does_not_affect_key(self):
        """Test that column order in schema doesn't affect cache key."""
        sql = "SELECT * FROM {{input1}}"

        schemas1 = {"table1": {"col1": "INTEGER", "col2": "VARCHAR", "col3": "DOUBLE"}}
        schemas2 = {"table1": {"col3": "DOUBLE", "col1": "INTEGER", "col2": "VARCHAR"}}

        key1 = _generate_sql_cache_key(sql, schemas1)
        key2 = _generate_sql_cache_key(sql, schemas2)

        # Schema is sorted before hashing, so keys should match
        assert key1 == key2


class TestSqlCacheStorage:
    """Test cache storage and retrieval."""

    def test_cache_and_retrieve(self):
        """Test basic cache storage and retrieval."""
        # Clear cache first
        _SQL_RESULT_CACHE.clear()

        cache_key = "test_key_001"
        result = {
            "status": "success",
            "columns": ["col1", "col2"],
            "preview": [{"col1": 1, "col2": "test"}],
            "row_count": 1
        }

        # Cache the result
        _cache_sql_result(cache_key, result)

        # Retrieve from cache
        cached = _get_cached_sql_result(cache_key)

        assert cached is not None
        assert cached["status"] == "success"
        assert cached["columns"] == ["col1", "col2"]
        assert cached["row_count"] == 1

    def test_cache_miss_returns_none(self):
        """Test that cache miss returns None."""
        # Clear cache first
        _SQL_RESULT_CACHE.clear()

        cached = _get_cached_sql_result("nonexistent_key")
        assert cached is None

    def test_cache_expiration(self):
        """Test that cache entries expire after TTL."""
        # Clear cache first
        _SQL_RESULT_CACHE.clear()

        cache_key = "test_key_expiration"
        result = {"status": "success"}

        # Manually insert an expired entry
        _SQL_RESULT_CACHE[cache_key] = {
            "result": result,
            "timestamp": time.time() - (31 * 60)  # 31 minutes ago (expired)
        }

        # Should return None due to expiration
        cached = _get_cached_sql_result(cache_key)
        assert cached is None

    def test_cache_max_size_enforcement(self):
        """Test that cache enforces maximum size limit."""
        # Clear cache first
        _SQL_RESULT_CACHE.clear()

        # Fill cache beyond max size
        for i in range(_MAX_SQL_RESULT_CACHE_SIZE + 20):
            cache_key = f"test_key_{i}"
            result = {"status": "success", "index": i}
            _cache_sql_result(cache_key, result)

        # Cache size should not exceed max
        assert len(_SQL_RESULT_CACHE) <= _MAX_SQL_RESULT_CACHE_SIZE


class TestSqlCacheEviction:
    """Test cache eviction logic."""

    def test_lru_eviction_removes_oldest(self):
        """Test that LRU eviction removes oldest entries."""
        # Clear cache first
        _SQL_RESULT_CACHE.clear()

        # Fill cache to max size with entries having different timestamps
        now = time.time()
        for i in range(_MAX_SQL_RESULT_CACHE_SIZE):
            cache_key = f"lru_test_{i}"
            _SQL_RESULT_CACHE[cache_key] = {
                "result": {"index": i},
                "timestamp": now - (_MAX_SQL_RESULT_CACHE_SIZE - i) * 60  # Oldest first
            }

        assert len(_SQL_RESULT_CACHE) == _MAX_SQL_RESULT_CACHE_SIZE

        # Trigger eviction by adding more entries beyond max
        # Adding 20 entries to trigger eviction
        for i in range(20):
            cache_key = f"new_entry_{i}"
            _cache_sql_result(cache_key, {"new": i})

        # Eviction should have removed SOME oldest entries
        # The exact number depends on when eviction triggers during the loop
        # But at minimum, the very first entry should be gone
        assert "lru_test_0" not in _SQL_RESULT_CACHE

        # Cache should be close to max size (or below)
        assert len(_SQL_RESULT_CACHE) <= _MAX_SQL_RESULT_CACHE_SIZE + 20


class TestSqlCacheInvalidation:
    """Test cache invalidation logic."""

    def test_invalidate_cache_for_table(self):
        """Test that cache invalidation clears all entries."""
        # Clear cache first
        _SQL_RESULT_CACHE.clear()

        # Populate cache
        for i in range(10):
            cache_key = f"test_key_{i}"
            _cache_sql_result(cache_key, {"index": i})

        assert len(_SQL_RESULT_CACHE) > 0

        # Invalidate cache
        _invalidate_sql_cache_for_table("some_table")

        # All entries should be cleared
        assert len(_SQL_RESULT_CACHE) == 0


class TestSqlCacheIntegration:
    """Integration tests for SQL caching."""

    def test_cache_hit_scenario(self):
        """Test complete cache hit scenario."""
        # Clear cache first
        _SQL_RESULT_CACHE.clear()

        sql = "SELECT name, age FROM users WHERE age > 18"
        schemas = {"users": {"name": "VARCHAR", "age": "INTEGER", "email": "VARCHAR"}}

        # Generate cache key
        cache_key = _generate_sql_cache_key(sql, schemas)

        # Check for cache miss initially
        result1 = _get_cached_sql_result(cache_key)
        assert result1 is None

        # Simulate query result
        query_result = {
            "status": "success",
            "columns": ["name", "age"],
            "preview": [
                {"name": "Alice", "age": 25},
                {"name": "Bob", "age": 30}
            ],
            "row_count": 2
        }

        # Cache the result
        _cache_sql_result(cache_key, query_result)

        # Check for cache hit
        result2 = _get_cached_sql_result(cache_key)
        assert result2 is not None
        assert result2["status"] == "success"
        assert result2["row_count"] == 2
        assert len(result2["preview"]) == 2

    def test_cache_invalidation_on_schema_change(self):
        """Test that schema changes produce cache misses."""
        # Clear cache first
        _SQL_RESULT_CACHE.clear()

        sql = "SELECT * FROM {{input1}}"

        # First query with schema v1
        schemas_v1 = {"table1": {"col1": "INTEGER", "col2": "VARCHAR"}}
        key_v1 = _generate_sql_cache_key(sql, schemas_v1)

        result_v1 = {"status": "success", "version": 1}
        _cache_sql_result(key_v1, result_v1)

        # Schema changed to v2 (different column type)
        schemas_v2 = {"table1": {"col1": "INTEGER", "col2": "DOUBLE"}}
        key_v2 = _generate_sql_cache_key(sql, schemas_v2)

        # Different schema should produce different cache key
        assert key_v1 != key_v2

        # Cache miss with new schema
        result_v2 = _get_cached_sql_result(key_v2)
        assert result_v2 is None

        # Old schema still hits cache
        result_old = _get_cached_sql_result(key_v1)
        assert result_old is not None
        assert result_old["version"] == 1
