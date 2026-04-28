"""
Database Connector Base

Provides base database connector functionality with connection management,
schema discovery, query execution, and security features.
"""

import re
from typing import Dict, Any, List, Optional, Iterator, Tuple
from urllib.parse import urlparse, parse_qs

from src.core.connectors.base import BaseConnector
from src.core.database.exceptions import ConnectionError, ConnectionValidationError


class DatabaseConnector(BaseConnector):
    """
    Base database connector providing common functionality for all database types.

    Features:
    - Connection string validation and parsing
    - Schema discovery (tables, columns, constraints)
    - Query execution with streaming support
    - Transaction management
    - Security features (SQL injection prevention, credential sanitization)
    """

    # SQL injection patterns to detect in connection strings
    SQL_INJECTION_PATTERNS = [
        r"';",  # Statement terminator with quote
        r"DROP\s+TABLE",  # DROP TABLE command
        r"DROP\s+DATABASE",  # DROP DATABASE command
        r"EXEC\s*\(",  # EXEC command
        r"--",  # SQL comment
        r"/\*",  # SQL comment start
        r"\x00",  # Null byte
        r"\\x[0-9a-f]{2}",  # Hex escape sequences
    ]

    def __init__(self, connection_string: Optional[str] = None, **kwargs):
        """
        Initialize database connector.

        Args:
            connection_string: Database connection string
            **kwargs: Additional connection parameters
        """
        self.connection_string = connection_string
        self._connection = None
        self._connected = False
        self._connection_params = kwargs

    @property
    def connected(self) -> bool:
        """Check if connector is connected to database"""
        return self._connected

    def connect(self, **kwargs) -> None:
        """
        Establish connection to database.

        Must be implemented by subclasses.

        Args:
            **kwargs: Connection parameters

        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        raise NotImplementedError("Subclasses must implement connect()")

    def disconnect(self) -> None:
        """Close database connection"""
        if self._connection:
            self._connection.close()
            self._connection = None
            self._connected = False

    def read(self, **kwargs) -> Iterator[Dict[str, Any]]:
        """
        Read data from database.

        Args:
            **kwargs: Query parameters

        Yields:
            Dictionary representing a single row
        """
        query = kwargs.get('query', '')
        params = kwargs.get('params')

        results = self.execute_select(query, params=params)
        for row in results:
            # Convert tuple to dict using column names
            if row:
                yield dict(row) if isinstance(row, dict) else {'_data': row}

    def validate(self, **kwargs) -> bool:
        """
        Validate database configuration.

        Args:
            **kwargs: Validation parameters

        Returns:
            True if valid

        Raises:
            ConnectionValidationError: If validation fails
        """
        connection_string = kwargs.get('connection_string', self.connection_string)
        db_type = kwargs.get('db_type', 'postgresql')

        if not connection_string:
            raise ConnectionValidationError("Connection string is required")

        return self.validate_connection_string(connection_string, db_type)

    def get_metadata(self, **kwargs) -> Dict[str, Any]:
        """
        Get metadata about database.

        Args:
            **kwargs: Metadata query parameters

        Returns:
            Dictionary with metadata (tables, version, etc.)
        """
        return {
            'connected': self.connected,
            'connection_string': self.sanitize_connection_string(self.connection_string) if self.connection_string else None,
            'type': self.__class__.__name__,
        }

    def validate_connection_string(self, connection_string: str, db_type: str = 'postgresql') -> bool:
        """
        Validate database connection string format and security.

        Args:
            connection_string: Connection string to validate
            db_type: Database type ('postgresql' or 'mysql')

        Returns:
            True if valid

        Raises:
            ConnectionValidationError: If connection string is invalid or malicious
        """
        if not connection_string or not isinstance(connection_string, str):
            raise ConnectionValidationError("Invalid connection string format: connection string must be a non-empty string")

        # Check for SQL injection patterns
        for pattern in self.SQL_INJECTION_PATTERNS:
            if re.search(pattern, connection_string, re.IGNORECASE):
                raise ConnectionValidationError(
                    f"Potentially malicious connection string detected: pattern '{pattern}'"
                )

        # Validate URL format
        try:
            parsed = urlparse(connection_string)
            if not parsed.scheme or not parsed.netloc:
                raise ConnectionValidationError(
                    "Invalid connection string format: missing scheme or host"
                )

            # Validate scheme for database type
            valid_schemes = {
                'postgresql': ['postgresql', 'postgres'],
                'mysql': ['mysql'],
                'mssql': ['mssql', 'mssql+pyodbc', 'sqlserver'],
            }

            if db_type in valid_schemes:
                if parsed.scheme not in valid_schemes[db_type]:
                    raise ConnectionValidationError(
                        f"Invalid scheme '{parsed.scheme}' for {db_type} connection"
                    )

        except Exception as e:
            if isinstance(e, ConnectionValidationError):
                raise
            raise ConnectionValidationError(f"Invalid connection string format: {e}")

        return True

    def sanitize_connection_string(self, connection_string: str) -> str:
        """
        Sanitize connection string for logging by masking password.

        Args:
            connection_string: Connection string to sanitize

        Returns:
            Sanitized connection string with password masked
        """
        if not connection_string:
            return connection_string

        try:
            parsed = urlparse(connection_string)

            # Reconstruct URL with masked password
            if parsed.password:
                # Replace password with asterisks
                netloc = f"{parsed.username}:***@{parsed.hostname}"
                if parsed.port:
                    netloc = f"{netloc}:{parsed.port}"

                sanitized = parsed._replace(netloc=netloc).geturl()
                return sanitized

        except Exception:
            # If parsing fails, return original
            pass

        return connection_string

    def parse_connection_string(self, connection_string: str) -> Dict[str, Any]:
        """
        Parse connection string into components.

        Args:
            connection_string: Connection string to parse

        Returns:
            Dictionary with connection components (scheme, user, password, host, port, database, params)
        """
        parsed = urlparse(connection_string)

        components = {
            'scheme': parsed.scheme,
            'user': parsed.username,
            'password': parsed.password,
            'host': parsed.hostname,
            'port': parsed.port,
            'database': parsed.path.lstrip('/') if parsed.path else None,
            'params': parse_qs(parsed.query),
        }

        # Extract sslmode from params for easy access
        if 'sslmode' in components['params']:
            components['sslmode'] = components['params']['sslmode'][0]
        elif 'ssl-mode' in components['params']:
            components['sslmode'] = components['params']['ssl-mode'][0]

        return components

    def list_tables(self) -> List[str]:
        """
        List all tables in the database.

        Returns:
            List of table names

        Raises:
            ConnectionError: If not connected
        """
        if not self._connected:
            raise ConnectionError("Not connected to database")

        query = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
            ORDER BY table_name
        """

        results = self._execute_query(query)
        return [row[0] for row in results]

    def get_table_schema(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Get schema information for a table.

        Args:
            table_name: Name of the table

        Returns:
            List of column information dictionaries

        Raises:
            ConnectionError: If not connected
        """
        if not self._connected:
            raise ConnectionError("Not connected to database")

        query = """
            SELECT
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_name = %s
            ORDER BY ordinal_position
        """

        results = self._execute_query(query, params=[table_name])

        schema = []
        for row in results:
            schema.append({
                'name': row[0],
                'type': row[1],
                'nullable': row[2] == 'YES',
                'default': row[3],
            })

        return schema

    def get_primary_keys(self) -> List[Tuple[str, str]]:
        """
        Get all primary key constraints.

        Returns:
            List of (table_name, column_name) tuples

        Raises:
            ConnectionError: If not connected
        """
        if not self._connected:
            raise ConnectionError("Not connected to database")

        query = """
            SELECT
                tc.table_name,
                kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            WHERE tc.constraint_type = 'PRIMARY KEY'
            ORDER BY tc.table_name, kcu.column_name
        """

        results = self._execute_query(query)
        return [(row[0], row[1]) for row in results]

    def get_foreign_keys(self) -> List[Dict[str, Any]]:
        """
        Get all foreign key constraints.

        Returns:
            List of foreign key relationship dictionaries

        Raises:
            ConnectionError: If not connected
        """
        if not self._connected:
            raise ConnectionError("Not connected to database")

        query = """
            SELECT
                tc.table_name AS from_table,
                kcu.column_name AS from_column,
                ccu.table_name AS to_table,
                ccu.column_name AS to_column
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage ccu
                ON ccu.constraint_name = tc.constraint_name
                AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
            ORDER BY tc.table_name, kcu.column_name
        """

        results = self._execute_query(query)

        foreign_keys = []
        for row in results:
            foreign_keys.append({
                'from_table': row[0],
                'from_column': row[1],
                'to_table': row[2],
                'to_column': row[3],
            })

        return foreign_keys

    def execute_select(self, query: str, params: Optional[List[Any]] = None) -> List[Tuple]:
        """
        Execute SELECT query.

        Args:
            query: SQL query
            params: Query parameters

        Returns:
            List of result tuples

        Raises:
            ConnectionError: If not connected
        """
        if not self._connected:
            raise ConnectionError("Not connected to database")

        return self._execute_query(query, params=params)

    def execute_query_stream(self, query: str, params: Optional[List[Any]] = None) -> Iterator[Tuple]:
        """
        Execute query and stream results.

        Args:
            query: SQL query
            params: Query parameters

        Yields:
            Result tuples

        Raises:
            ConnectionError: If not connected
        """
        if not self._connected:
            raise ConnectionError("Not connected to database")

        results = self._execute_query(query, params=params)
        for row in results:
            yield row

    def execute_insert(self, query: str, params: Optional[List[Any]] = None) -> int:
        """
        Execute INSERT query.

        Args:
            query: SQL query
            params: Query parameters

        Returns:
            Number of affected rows

        Raises:
            ConnectionError: If not connected
        """
        if not self._connected:
            raise ConnectionError("Not connected to database")

        return self._execute_query(query, params=params)

    def execute_update(self, query: str, params: Optional[List[Any]] = None) -> int:
        """
        Execute UPDATE query.

        Args:
            query: SQL query
            params: Query parameters

        Returns:
            Number of affected rows

        Raises:
            ConnectionError: If not connected
        """
        if not self._connected:
            raise ConnectionError("Not connected to database")

        return self._execute_query(query, params=params)

    def execute_delete(self, query: str, params: Optional[List[Any]] = None) -> int:
        """
        Execute DELETE query.

        Args:
            query: SQL query
            params: Query parameters

        Returns:
            Number of affected rows

        Raises:
            ConnectionError: If not connected
        """
        if not self._connected:
            raise ConnectionError("Not connected to database")

        return self._execute_query(query, params=params)

    def begin_transaction(self) -> None:
        """
        Begin a new transaction.

        Raises:
            ConnectionError: If not connected
        """
        if not self._connected:
            raise ConnectionError("Not connected to database")

        self._execute_query("BEGIN")

    def commit_transaction(self) -> None:
        """
        Commit current transaction.

        Raises:
            ConnectionError: If not connected
        """
        if not self._connected:
            raise ConnectionError("Not connected to database")

        self._execute_query("COMMIT")

    def rollback_transaction(self) -> None:
        """
        Rollback current transaction.

        Raises:
            ConnectionError: If not connected
        """
        if not self._connected:
            raise ConnectionError("Not connected to database")

        self._execute_query("ROLLBACK")

    def transaction(self):
        """
        Context manager for transaction handling.

        Yields:
            None

        Example:
            with connector.transaction():
                connector.execute_insert(...)
                connector.execute_update(...)
        """
        class TransactionContext:
            def __init__(self, connector):
                self._connector = connector

            def __enter__(self):
                self._connector.begin_transaction()
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                if exc_type is not None:
                    self._connector.rollback_transaction()
                    return False  # Don't suppress exception
                else:
                    self._connector.commit_transaction()
                    return True

        return TransactionContext(self)

    def _execute_query(self, query: str, params: Optional[List[Any]] = None) -> Any:
        """
        Execute a database query (internal method).

        Must be implemented by subclasses to handle specific database execution.

        Args:
            query: SQL query
            params: Query parameters

        Returns:
            Query results (implementation-dependent)

        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        raise NotImplementedError("Subclasses must implement _execute_query()")
