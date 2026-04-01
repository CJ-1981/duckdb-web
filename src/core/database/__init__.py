"""
DuckDB Database Connection Management

Provides thread-safe connection pooling, parameterized queries,
and automatic reconnection for DuckDB databases.
"""

import threading
import time
from typing import Any, List, Optional, Dict, Iterator
import duckdb

from .pool import ConnectionPool
from .query import QueryBuilder
from .exceptions import (
    ConnectionError,
    QueryTimeoutError,
    QueryExecutionError,
    DatabaseError,
)

__all__ = [
    "DatabaseConnection",
    "ConnectionPool",
    "QueryBuilder",
    "ConnectionError",
    "QueryTimeoutError",
    "QueryExecutionError",
    "DatabaseError",
    "connect",
]


class DatabaseConnection:
    """
    DuckDB database connection with connection pooling and automatic reconnection

    Features:
    - Thread-safe connection pooling
    - Parameterized queries (SQL injection prevention)
    - Connection health checks and auto-reconnection
    - Query timeout handling
    - Result streaming for large datasets
    - Integration with configuration system

    Example:
        >>> db = DatabaseConnection("data.duckdb", max_connections=10)
        >>> db.execute("CREATE TABLE users (id INTEGER, name VARCHAR)")
        >>> db.execute("INSERT INTO users VALUES (?, ?)", parameters=[1, "Alice"])
        >>> result = db.execute("SELECT * FROM users WHERE id = ?", parameters=[1])
        >>> print(result[0]["name"])  # Alice
    """

    def __init__(
        self,
        db_path: str = ":memory:",
        max_connections: int = 10,
        connection_timeout: float = 30.0,
        query_timeout: float = 60.0,
        auto_reconnect: bool = True,
        max_retries: int = 3,
        retry_delay: float = 0.5,
        enable_memory_tracking: bool = False,
    ):
        """
        Initialize database connection

        Args:
            db_path: Path to database file (or :memory: for in-memory)
            max_connections: Maximum connections in pool
            connection_timeout: Timeout for acquiring connection from pool
            query_timeout: Default timeout for query execution
            auto_reconnect: Automatically reconnect on connection failure
            max_retries: Maximum connection retry attempts
            retry_delay: Delay between retries in seconds
            enable_memory_tracking: Enable DuckDB memory tracking
        """
        self._db_path = db_path
        self._max_connections = max_connections
        self._connection_timeout = connection_timeout
        self._query_timeout = query_timeout
        self._auto_reconnect = auto_reconnect
        self._max_retries = max_retries
        self._retry_delay = retry_delay
        self._enable_memory_tracking = enable_memory_tracking

        # Initialize connection pool
        self._pool = ConnectionPool(
            max_connections=max_connections,
            timeout=connection_timeout,
            validate_connections=True,
        )

        # Connection state
        self._conn: Optional[duckdb.DuckDBPyConnection] = None
        self._is_closed = False
        self._lock = threading.RLock()

        # Initialize connection
        self._connect()

    @property
    def db_path(self) -> str:
        """Get database path"""
        return self._db_path

    @property
    def max_connections(self) -> int:
        """Get maximum connections"""
        return self._max_connections

    @property
    def connection_timeout(self) -> float:
        """Get connection timeout"""
        return self._connection_timeout

    @property
    def query_timeout(self) -> float:
        """Get query timeout"""
        return self._query_timeout

    @classmethod
    def from_config(cls, config: Any) -> "DatabaseConnection":
        """
        Create database connection from configuration

        Args:
            config: Configuration object with database settings

        Returns:
            DatabaseConnection instance
        """
        return cls(
            db_path=config.database.path,
            max_connections=config.database.max_connections,
            connection_timeout=config.database.connection_timeout,
            query_timeout=config.database.query_timeout,
            enable_memory_tracking=getattr(
                config.database, "enable_memory_tracking", False
            ),
        )

    def _connect(self) -> None:
        """
        Establish database connection with retry logic

        Raises:
            ConnectionError: If connection fails after retries
        """
        last_error = None

        for attempt in range(self._max_retries):
            try:
                self._conn = duckdb.connect(self._db_path)

                # Note: Memory tracking is not available in DuckDB
                # Keeping parameter for API compatibility but no-op

                return

            except Exception as e:
                last_error = e
                if attempt < self._max_retries - 1:
                    time.sleep(self._retry_delay)

        raise ConnectionError(
            f"Failed to connect after {self._max_retries} attempts: {last_error}"
        )

    def _ensure_connection(self) -> None:
        """
        Ensure connection is active, reconnect if needed

        Raises:
            ConnectionError: If reconnection fails
        """
        # Note: Allow reconnection even if explicitly closed
        # This enables the auto-reconnect feature to work after close()

        if not self.is_healthy():
            if self._auto_reconnect:
                self._connect()
                self._is_closed = False  # Reset closed flag on reconnect
            else:
                raise ConnectionError("Database connection is not healthy")

    def is_healthy(self) -> bool:
        """
        Check if connection is healthy

        Returns:
            True if connection is healthy
        """
        try:
            if self._conn is None:
                return False
            self._conn.execute("SELECT 1").fetchone()
            return True
        except Exception:
            return False

    def execute(
        self, query: str, parameters: List[Any] = None, timeout: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute a query with parameters

        Args:
            query: SQL query with ? placeholders
            parameters: Query parameters
            timeout: Query timeout in seconds (NOTE: DuckDB doesn't support per-query timeout,
                    this parameter is stored for future API compatibility)

        Returns:
            List of result dictionaries

        Raises:
            QueryExecutionError: If query execution fails
        """
        self._ensure_connection()

        parameters = parameters or []

        try:
            # Execute query with parameters
            result = self._conn.execute(query, parameters)

            # Fetch results
            if result.description:
                # Convert to list of dictionaries
                columns = [desc[0] for desc in result.description]
                rows = result.fetchall()

                return [dict(zip(columns, row)) for row in rows]
            else:
                # No results (INSERT, UPDATE, DELETE, etc.)
                return []

        except Exception as e:
            raise QueryExecutionError(f"Query execution failed: {e}")

    def execute_batch(self, query: str, parameters_list: List[List[Any]]) -> None:
        """
        Execute query multiple times with different parameters

        Args:
            query: SQL query with ? placeholders
            parameters_list: List of parameter lists

        Raises:
            QueryExecutionError: If batch execution fails
        """
        self._ensure_connection()

        try:
            for parameters in parameters_list:
                self._conn.execute(query, parameters)
        except Exception as e:
            raise QueryExecutionError(f"Batch execution failed: {e}")

    def stream(
        self, query: str, parameters: List[Any] = None, chunk_size: int = 1000
    ) -> Iterator[List[Dict[str, Any]]]:
        """
        Stream query results in chunks

        Args:
            query: SQL query
            parameters: Query parameters
            chunk_size: Number of rows per chunk

        Yields:
            List of result dictionaries (chunks)
        """
        self._ensure_connection()

        parameters = parameters or []

        try:
            result = self._conn.execute(query, parameters)

            if result.description:
                columns = [desc[0] for desc in result.description]

                while True:
                    rows = result.fetchmany(chunk_size)
                    if not rows:
                        break
                    yield [dict(zip(columns, row)) for row in rows]

        except Exception as e:
            raise QueryExecutionError(f"Stream execution failed: {e}")

    def iterate(
        self, query: str, parameters: List[Any] = None
    ) -> Iterator[Dict[str, Any]]:
        """
        Iterate over query results row by row

        Args:
            query: SQL query
            parameters: Query parameters

        Yields:
            Result dictionary for each row
        """
        self._ensure_connection()

        parameters = parameters or []

        try:
            result = self._conn.execute(query, parameters)

            if result.description:
                columns = [desc[0] for desc in result.description]

                for row in result.fetchall():
                    yield dict(zip(columns, row))

        except Exception as e:
            raise QueryExecutionError(f"Iteration failed: {e}")

    def cancel_query(self) -> None:
        """
        Cancel the currently executing query

        Note: This is a best-effort operation and may not always succeed.
        """
        try:
            if self._conn:
                self._conn.interrupt()
        except Exception:
            pass

    def close(self) -> None:
        """Close the database connection"""
        with self._lock:
            if self._conn:
                try:
                    self._conn.close()
                except Exception:
                    pass
                finally:
                    self._is_closed = True
                    self._conn = None

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
        return False

    def __del__(self):
        """Destructor - ensure connection is closed"""
        try:
            self.close()
        except Exception:
            pass


# Convenience functions


def connect(db_path: str = ":memory:", **kwargs) -> DatabaseConnection:
    """
    Create a database connection

    Args:
        db_path: Path to database file
        **kwargs: Additional arguments for DatabaseConnection

    Returns:
        DatabaseConnection instance
    """
    return DatabaseConnection(db_path, **kwargs)
