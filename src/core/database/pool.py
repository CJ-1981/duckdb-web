"""
Connection Pool for DuckDB

Thread-safe connection pool with health checking and automatic reconnection.
"""

import threading
import time
import duckdb
from typing import Optional, List
from contextlib import contextmanager

from .exceptions import ConnectionError, PoolExhaustedError, ConnectionValidationError


class PooledConnection:
    """Wrapper for a pooled connection"""

    def __init__(self, conn: duckdb.DuckDBPyConnection, pool: "ConnectionPool"):
        self._conn = conn
        self._pool = pool
        self._in_use = False
        self._created_at = time.time()
        self._last_used = time.time()

    @property
    def connection(self) -> duckdb.DuckDBPyConnection:
        """Get the underlying connection"""
        return self._conn

    @property
    def in_use(self) -> bool:
        """Check if connection is in use"""
        return self._in_use

    @in_use.setter
    def in_use(self, value: bool):
        """Set connection in-use status"""
        self._in_use = value
        if value:
            self._last_used = time.time()

    @property
    def age(self) -> float:
        """Get connection age in seconds"""
        return time.time() - self._created_at

    @property
    def idle_time(self) -> float:
        """Get connection idle time in seconds"""
        return time.time() - self._last_used

    def is_valid(self) -> bool:
        """Check if connection is valid"""
        try:
            # Execute simple query to test connection
            self._conn.execute("SELECT 1").fetchone()
            return True
        except Exception:
            return False


class ConnectionPool:
    """
    Thread-safe connection pool for DuckDB

    Features:
    - Configurable maximum connections
    - Connection validation
    - Automatic cleanup of stale connections
    - Thread-safe concurrent access
    """

    def __init__(
        self,
        max_connections: int = 10,
        timeout: float = 30.0,
        validate_connections: bool = True,
        health_check_interval: float = 60.0,
        max_connection_age: float = 3600.0,
    ):
        """
        Initialize connection pool

        Args:
            max_connections: Maximum number of connections in pool
            timeout: Timeout in seconds for acquiring connection
            validate_connections: Whether to validate connections before use
            health_check_interval: Interval for health checks
            max_connection_age: Maximum age of connection before removal
        """
        self._max_connections = max_connections
        self._timeout = timeout
        self._validate_connections = validate_connections
        self._health_check_interval = health_check_interval
        self._max_connection_age = max_connection_age

        self._pool: List[PooledConnection] = []
        self._lock = threading.RLock()
        self._condition = threading.Condition(self._lock)

    @property
    def max_connections(self) -> int:
        """Get maximum connections"""
        return self._max_connections

    @property
    def active_connections(self) -> int:
        """Get number of active connections"""
        with self._lock:
            return sum(1 for conn in self._pool if conn.in_use)

    @property
    def idle_connections(self) -> int:
        """Get number of idle connections"""
        with self._lock:
            return sum(1 for conn in self._pool if not conn.in_use)

    def acquire(self, db_path: str = ":memory:") -> duckdb.DuckDBPyConnection:
        """
        Acquire a connection from the pool

        Args:
            db_path: Path to database file (or :memory:)

        Returns:
            DuckDB connection

        Raises:
            PoolExhaustedError: If no connection available within timeout
        """
        deadline = time.time() + self._timeout

        with self._condition:
            while True:
                # Try to find idle connection
                for pooled_conn in self._pool:
                    if not pooled_conn.in_use:
                        # Validate if enabled
                        if self._validate_connections and not pooled_conn.is_valid():
                            # Remove invalid connection
                            self._pool.remove(pooled_conn)
                            continue

                        # Mark as in use and return
                        pooled_conn.in_use = True
                        return pooled_conn.connection

                # No idle connection available
                if len(self._pool) < self._max_connections:
                    # Create new connection
                    try:
                        conn = duckdb.connect(db_path)
                        pooled_conn = PooledConnection(conn, self)
                        pooled_conn.in_use = True
                        self._pool.append(pooled_conn)
                        return conn
                    except Exception as e:
                        raise ConnectionError(f"Failed to create connection: {e}")

                # Pool exhausted, wait or timeout
                remaining = deadline - time.time()
                if remaining <= 0:
                    raise PoolExhaustedError(
                        f"Connection pool exhausted after {self._timeout}s timeout. "
                        f"Active: {self.active_connections}, Max: {self._max_connections}"
                    )

                # Wait for connection to become available
                self._condition.wait(timeout=remaining)

    def release(self, conn: duckdb.DuckDBPyConnection) -> None:
        """
        Release a connection back to the pool

        Args:
            conn: Connection to release
        """
        with self._condition:
            # Find the pooled connection
            for pooled_conn in self._pool:
                if pooled_conn.connection == conn:
                    pooled_conn.in_use = False
                    self._condition.notify()
                    return

    def is_connection_valid(self, conn: duckdb.DuckDBPyConnection) -> bool:
        """
        Check if connection is valid

        Args:
            conn: Connection to validate

        Returns:
            True if connection is valid
        """
        try:
            conn.execute("SELECT 1").fetchone()
            return True
        except Exception:
            return False

    def clean_stale_connections(self) -> None:
        """
        Remove stale connections from pool

        Stale connections are those that exceed max_connection_age.
        """
        with self._lock:
            stale_connections = [
                conn
                for conn in self._pool
                if not conn.in_use and conn.idle_time > self._max_connection_age
            ]

            for conn in stale_connections:
                try:
                    conn.connection.close()
                except Exception:
                    pass
                self._pool.remove(conn)

    def close_all(self) -> None:
        """Close all connections in the pool"""
        with self._lock:
            for pooled_conn in self._pool:
                try:
                    pooled_conn.connection.close()
                except Exception:
                    pass
            self._pool.clear()

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close_all()
        return False
