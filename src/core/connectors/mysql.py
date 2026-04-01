"""
MySQL Connector

Provides MySQL-specific connector implementation using pymysql.
"""

from typing import Any, List, Optional, Tuple
from contextlib import contextmanager

try:
    import pymysql
    PYMYSQL_AVAILABLE = True
except ImportError:
    try:
        import mysql.connector as pymysql
        MYSQL_CONNECTOR_AVAILABLE = True
        PYMYSQL_AVAILABLE = True
    except ImportError:
        PYMYSQL_AVAILABLE = False
        pymysql = None

from src.core.connectors.database import DatabaseConnector
from src.core.database.exceptions import ConnectionError


class MySQLConnector(DatabaseConnector):
    """
    MySQL database connector.

    Features:
    - pymysql integration (or mysql-connector-python as fallback)
    - SSL/TLS support
    - MySQL-specific data types (BLOB, JSON, etc.)
    - LOAD DATA INFILE for bulk import
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
        ssl_mode: Optional[str] = None,
        charset: str = 'utf8mb4',
        connection_timeout: float = 30.0,
        connection_pool=None,
        **kwargs
    ):
        """
        Initialize MySQL connector.

        Args:
            connection_string: MySQL connection string
            host: Database host
            port: Database port (default: 3306)
            database: Database name
            user: Database user
            password: Database password
            ssl_mode: SSL mode ('DISABLED', 'PREFERRED', 'REQUIRED', 'VERIFY_CA', 'VERIFY_IDENTITY')
            charset: Character set (default: utf8mb4)
            connection_timeout: Connection timeout in seconds
            connection_pool: Optional connection pool instance
            **kwargs: Additional connection parameters
        """
        super().__init__(connection_string, **kwargs)

        # Allow mocking for tests
        if not PYMYSQL_AVAILABLE and not kwargs.get('_allow_mock', False):
            raise ImportError(
                "pymysql or mysql-connector-python is required for MySQL connector. "
                "Install with: pip install pymysql"
            )

        self._host = host
        self._port = port or 3306
        self._database = database
        self._user = user
        self._password = password
        self._ssl_mode = ssl_mode
        self._charset = charset
        self._connection_timeout = connection_timeout
        self._connection_pool = connection_pool

        # Build connection string from components if not provided
        if not connection_string and all([host, database]):
            self.connection_string = self._build_connection_string()

    @classmethod
    def from_config(cls, config) -> 'MySQLConnector':
        """
        Create connector from configuration object.

        Args:
            config: Configuration object with database.mysql attributes

        Returns:
            MySQLConnector instance
        """
        return cls(
            host=config.database.mysql.host,
            port=config.database.mysql.port,
            database=config.database.mysql.database,
            user=config.database.mysql.user,
            password=config.database.mysql.password,
            ssl_mode=config.database.mysql.ssl_mode,
        )

    def _build_connection_string(self) -> str:
        """Build connection string from components"""
        auth = f"{self._user}:{self._password}@" if self._user else ""
        port_part = f":{self._port}" if self._port else ""
        ssl_part = f"?ssl-mode={self._ssl_mode}" if self._ssl_mode else ""

        return f"mysql://{auth}{self._host}{port_part}/{self._database}{ssl_part}"

    def connect(self, **kwargs) -> None:
        """
        Establish connection to MySQL database.

        Raises:
            ConnectionError: If connection fails
        """
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
                    'charset': self._charset,
                    'connect_timeout': self._connection_timeout,
                }

                # Add SSL mode from params
                if 'ssl-mode' in conn_params['params']:
                    kwargs_conn['ssl_mode'] = conn_params['params']['ssl-mode'][0]
            else:
                kwargs_conn = {
                    'host': self._host,
                    'port': self._port,
                    'database': self._database,
                    'user': self._user,
                    'password': self._password,
                    'charset': self._charset,
                    'ssl_mode': self._ssl_mode,
                    'connect_timeout': self._connection_timeout,
                }

            # Remove None values
            kwargs_conn = {k: v for k, v in kwargs_conn.items() if v is not None}

            # Establish connection
            self._connection = pymysql.connect(**kwargs_conn)
            self._connected = True

        except Exception as e:
            raise ConnectionError(f"Failed to connect to MySQL: {e}")

    def disconnect(self) -> None:
        """Close MySQL connection"""
        super().disconnect()

    @contextmanager
    def _get_cursor(self):
        """
        Get database cursor with context manager.

        Yields:
            pymysql cursor
        """
        cursor = self._connection.cursor()
        try:
            yield cursor
        finally:
            cursor.close()

    def _execute_query(self, query: str, params: Optional[List[Any]] = None) -> Any:
        """
        Execute MySQL query.

        Args:
            query: SQL query
            params: Query parameters

        Returns:
            Query results or row count
        """
        with self._get_cursor() as cursor:
            cursor.execute(query, params)

            # Return results for SELECT
            if query.strip().upper().startswith('SELECT'):
                return cursor.fetchall()
            # Return row count for INSERT/UPDATE/DELETE
            else:
                return cursor.rowcount

    def load_data_infile(
        self,
        table_name: str,
        file_path: str,
        fields_terminated_by: str = ",",
        lines_terminated_by: str = "\\n",
        ignore_lines: int = 0
    ) -> None:
        """
        Use LOAD DATA INFILE for bulk data import.

        Args:
            table_name: Target table name
            file_path: Path to CSV file
            fields_terminated_by: Field delimiter (default: comma)
            lines_terminated_by: Line delimiter (default: newline)
            ignore_lines: Number of lines to ignore from start (default: 0)

        Raises:
            ConnectionError: If not connected
        """
        if not self._connected:
            raise ConnectionError("Not connected to database")

        query = f"""
            LOAD DATA INFILE '{file_path}'
            INTO TABLE {table_name}
            FIELDS TERMINATED BY '{fields_terminated_by}'
            LINES TERMINATED BY '{lines_terminated_by}'
            IGNORE {ignore_lines} LINES
        """

        with self._get_cursor() as cursor:
            cursor.execute(query)

        self._connection.commit()

    def execute_select(self, query: str, params: Optional[List[Any]] = None) -> List[Tuple]:
        """
        Execute SELECT query with MySQL-specific optimizations.

        Args:
            query: SQL query
            params: Query parameters

        Returns:
            List of result tuples
        """
        return super().execute_select(query, params)

    def list_tables(self) -> List[str]:
        """
        List all tables in MySQL database.

        Returns:
            List of table names
        """
        if not self._connected:
            raise ConnectionError("Not connected to database")

        query = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = DATABASE()
            ORDER BY table_name
        """

        results = self._execute_query(query)
        return [row[0] for row in results]
