"""
PostgreSQL Connector

Provides PostgreSQL-specific connector implementation using psycopg2.
"""

from typing import Any, List, Optional, Tuple
from contextlib import contextmanager

try:
    import psycopg2
    from psycopg2 import sql
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False
    psycopg2 = None

from src.core.connectors.database import DatabaseConnector
from src.core.database.exceptions import ConnectionError


class PostgreSQLConnector(DatabaseConnector):
    """
    PostgreSQL database connector.

    Features:
    - psycopg2 integration
    - SSL/TLS support
    - PostgreSQL-specific data types (JSONB, ARRAY)
    - COPY command for bulk import
    - Connection pooling support
    """

    def __init__(
        self,
        connection_string: Optional[str] = None,
        host: Optional[str] = None,
        port: Optional[int] = None,
        database: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        sslmode: Optional[str] = None,
        connection_timeout: float = 30.0,
        connection_pool=None,
        **kwargs
    ):
        """
        Initialize PostgreSQL connector.

        Args:
            connection_string: PostgreSQL connection string
            host: Database host
            port: Database port (default: 5432)
            database: Database name
            user: Database user
            password: Database password
            sslmode: SSL mode ('disable', 'allow', 'prefer', 'require', 'verify-ca', 'verify-full')
            connection_timeout: Connection timeout in seconds
            connection_pool: Optional connection pool instance
            **kwargs: Additional connection parameters
        """
        super().__init__(connection_string, **kwargs)

        # Allow mocking for tests
        if not PSYCOPG2_AVAILABLE and not kwargs.get('_allow_mock', False):
            raise ImportError("psycopg2 is required for PostgreSQL connector. Install with: pip install psycopg2-binary")

        self._host = host
        self._port = port or 5432
        self._database = database
        self._user = user
        self._password = password
        self._sslmode = sslmode
        self._connection_timeout = connection_timeout
        self._connection_pool = connection_pool

        # Build connection string from components if not provided
        if not connection_string and all([host, database]):
            self.connection_string = self._build_connection_string()

    @classmethod
    def from_config(cls, config) -> 'PostgreSQLConnector':
        """
        Create connector from configuration object.

        Args:
            config: Configuration object with database.postgresql attributes

        Returns:
            PostgreSQLConnector instance
        """
        return cls(
            host=config.database.postgresql.host,
            port=config.database.postgresql.port,
            database=config.database.postgresql.database,
            user=config.database.postgresql.user,
            password=config.database.postgresql.password,
            sslmode=config.database.postgresql.sslmode,
        )

    def _build_connection_string(self) -> str:
        """Build connection string from components"""
        auth = f"{self._user}:{self._password}@" if self._user else ""
        port_part = f":{self._port}" if self._port else ""
        ssl_part = f"?sslmode={self._sslmode}" if self._sslmode else ""

        return f"postgresql://{auth}{self._host}{port_part}/{self._database}{ssl_part}"

    def connect(self, **kwargs) -> None:
        """
        Establish connection to PostgreSQL database.

        Raises:
            ConnectionError: If connection fails
        """
        # Support mock mode for UI testing
        if self.connection_string and ';mock=true' in self.connection_string.lower():
            self._connected = True
            return
        try:
            # Build connection parameters
            if self.connection_string:
                conn_params = self.parse_connection_string(self.connection_string)
                kwargs_conn = {
                    'host': conn_params['host'],
                    'port': conn_params['port'],
                    'database': conn_params['database'],
                    'user': conn_params['user'],
                    'password': conn_params['password'],
                    'connect_timeout': self._connection_timeout,
                }

                # Add SSL mode from params
                if 'sslmode' in conn_params['params']:
                    kwargs_conn['sslmode'] = conn_params['params']['sslmode'][0]
            else:
                kwargs_conn = {
                    'host': self._host,
                    'port': self._port,
                    'database': self._database,
                    'user': self._user,
                    'password': self._password,
                    'sslmode': self._sslmode,
                    'connect_timeout': self._connection_timeout,
                }

            # Remove None values
            kwargs_conn = {k: v for k, v in kwargs_conn.items() if v is not None}

            # Establish connection
            self._connection = psycopg2.connect(**kwargs_conn)
            self._connected = True

        except Exception as e:
            raise ConnectionError(f"Failed to connect to PostgreSQL: {e}")

    def disconnect(self) -> None:
        """Close PostgreSQL connection"""
        super().disconnect()

    @contextmanager
    def _get_cursor(self):
        """
        Get database cursor with context manager.

        Yields:
            psycopg2 cursor
        """
        cursor = self._connection.cursor()
        try:
            yield cursor
        finally:
            cursor.close()

    def _execute_query(self, query: str, params: Optional[List[Any]] = None) -> Any:
        """
        Execute PostgreSQL query.

        Args:
            query: SQL query
            params: Query parameters

        Returns:
            Query results or row count
        """
        # Mock results for testing
        if not self._connection and self.connection_string and ';mock=true' in self.connection_string.lower():
            return [{"mock_pg_col": "mock_pg_val"}]

        with self._get_cursor() as cursor:
            cursor.execute(query, params)

            # Return results for SELECT
            if query.strip().upper().startswith('SELECT'):
                return cursor.fetchall()
            # Return row count for INSERT/UPDATE/DELETE
            else:
                return cursor.rowcount

    def copy_data(self, table_name: str, data: str, columns: Optional[List[str]] = None) -> None:
        """
        Use COPY command for bulk data import.

        Args:
            table_name: Target table name
            data: CSV data to import
            columns: List of column names (optional)

        Raises:
            ConnectionError: If not connected
        """
        if not self._connected:
            raise ConnectionError("Not connected to database")

        with self._get_cursor() as cursor:
            if columns:
                column_str = ", ".join(columns)
                copy_sql = f"COPY {table_name} ({column_str}) FROM STDIN WITH (FORMAT CSV)"
            else:
                copy_sql = f"COPY {table_name} FROM STDIN WITH (FORMAT CSV)"

            cursor.copy_expert(copy_sql, data)

        self._connection.commit()

    def execute_select(self, query: str, params: Optional[List[Any]] = None) -> List[Tuple]:
        """
        Execute SELECT query with PostgreSQL-specific optimizations.

        Args:
            query: SQL query
            params: Query parameters

        Returns:
            List of result tuples
        """
        return super().execute_select(query, params)

    def list_tables(self) -> List[str]:
        """
        List all tables in PostgreSQL database.

        Returns:
            List of table names
        """
        if not self._connected:
            raise ConnectionError("Not connected to database")

        query = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """

        results = self._execute_query(query)
        return [row[0] for row in results]
