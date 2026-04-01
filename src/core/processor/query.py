"""
Query Execution Module

Provides query execution with:
- Result caching
- Query history tracking
- Parameterized query support
"""

import logging
from typing import Optional, List, Dict, Any
import time
import duckdb
import pandas as pd

logger = logging.getLogger(__name__)


class QueryExecutor:
    """
    Query executor with caching and history tracking
    """

    def __init__(
        self,
        connection: duckdb.DuckDBPyConnection,
        cache_enabled: bool = True,
        track_queries: bool = False,
        cache_ttl: int = 300,  # 5 minutes
    ):
        """
        Initialize query executor

        Args:
            connection: DuckDB connection
            cache_enabled: Enable result caching
            track_queries: Enable query history tracking
            cache_ttl: Cache time-to-live in seconds (default 300)
        """
        self._connection = connection
        self._cache_enabled = cache_enabled
        self._track_queries = track_queries
        self._cache_ttl = cache_ttl
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._query_history: List[Dict[str, Any]] = []

    def execute(
        self,
        query: str,
        parameters: Optional[List] = None,
        use_cache: bool = True
    ) -> pd.DataFrame:
        """
        Execute query with optional caching

        Args:
            query: SQL query
            parameters: Query parameters (optional)
            use_cache: Use cached result if available (default True)

        Returns:
            DataFrame with results
        """
        # Check cache first
        cache_key = self._make_cache_key(query, parameters)
        if use_cache and self._cache_enabled and cache_key in self._cache:
                cache_entry = self._cache[cache_key]
                if time.time() - cache_entry['timestamp'] < self._cache_ttl:
                    logger.debug(f"Cache hit for query")
                    return cache_entry['result'].copy()

        # Track query if enabled
        if self._track_queries:
            self._query_history.append({
                'query': query,
                'parameters': parameters,
                'timestamp': time.time()
            })

        # Execute query
        if parameters:
            result = self._connection.execute(query, parameters).df()
        else:
            result = self._connection.execute(query).df()

        # Cache result
        if self._cache_enabled and use_cache:
            self._cache[cache_key] = {
                'result': result.copy(),
                'timestamp': time.time()
            }

        return result

    def clear_cache(self) -> None:
        """Clear query result cache"""
        self._cache.clear()
        logger.info("Query cache cleared")

    def _make_cache_key(self, query: str, parameters: Optional[List] = None) -> str:
        """
        Generate cache key from query and parameters

        Args:
            query: SQL query
            parameters: Query parameters

        Returns:
            Cache key string
        """
        key = query
        if parameters:
            key += str(parameters)
        return str(hash(key))
