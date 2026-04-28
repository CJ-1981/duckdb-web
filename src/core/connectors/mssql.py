"""
SQL Server Connector

Provides SQL Server-specific connector implementation using pyodbc.
"""

import logging
from typing import Any, List, Optional, Tuple, Dict
from contextlib import contextmanager

try:
    import pyodbc
    PYODBC_AVAILABLE = True
except ImportError:
    PYODBC_AVAILABLE = False
    pyodbc = None

from .database import DatabaseConnector
from ..database.exceptions import ConnectionError

logger = logging.getLogger(__name__)

class MSSQLConnector(DatabaseConnector):
    """
    SQL Server database connector.

    Features:
    - pyodbc integration
    - Support for Trusted_Connection and standard auth
    - Schema discovery for SQL Server
    """

    def __init__(
        self,
        connection_string: Optional[str] = None,
        host: Optional[str] = None,
        port: Optional[int] = None,
        database: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        driver: str = '{ODBC Driver 17 for SQL Server}',
        trusted_connection: bool = False,
        **kwargs
    ):
        """
        Initialize SQL Server connector.

        Args:
            connection_string: Full ODBC connection string
            host: Database host
            port: Database port (default: 1433)
            database: Database name
            user: Database user
            password: Database password
            driver: ODBC driver name
            trusted_connection: Use Windows authentication
            **kwargs: Additional connection parameters
        """
        super().__init__(connection_string, **kwargs)

        if not PYODBC_AVAILABLE and not kwargs.get('_allow_mock', False):
            raise ImportError(
                "pyodbc is required for SQL Server connector. "
                "Install with: pip install pyodbc"
            )

        self._host = host
        self._port = port or 1433
        self._database = database
        self._user = user
        self._password = password
        self._driver = driver
        self._trusted_connection = trusted_connection

        # Build connection string if components provided
        if not connection_string and host:
            self.connection_string = self._build_connection_string()

    def _build_connection_string(self) -> str:
        """Build ODBC connection string from components"""
        parts = [
            f"DRIVER={self._driver}",
            f"SERVER={self._host},{self._port}",
            f"DATABASE={self._database}"
        ]
        
        if self._trusted_connection:
            parts.append("Trusted_Connection=yes")
        else:
            if self._user:
                parts.append(f"UID={self._user}")
            if self._password:
                parts.append(f"PWD={self._password}")
        
        return ";".join(parts)

    def connect(self, **kwargs) -> None:
        """Establish connection to SQL Server"""
        # Support mock mode for UI testing
        if ';mock=true' in self.connection_string.lower():
            self._connected = True
            logger.info("SQL Server Connector: Mock mode activated")
            return

        try:
            # SQL Server connection string is literal ODBC format
            # Use a shorter timeout by default (10s instead of 30s)
            connect_timeout = kwargs.get('timeout', 10)
            self._connection = pyodbc.connect(self.connection_string, timeout=connect_timeout)
            self._connected = True
            logger.info(f"Successfully connected to SQL Server at {self._host or 'remote'}")
        except Exception as e:
            raise ConnectionError(f"Failed to connect to SQL Server: {e}")

    def disconnect(self) -> None:
        """Close SQL Server connection"""
        super().disconnect()

    @contextmanager
    def _get_cursor(self):
        """Get database cursor with context manager"""
        if not self._connection:
            raise ConnectionError("Not connected to database")
        cursor = self._connection.cursor()
        try:
            yield cursor
        finally:
            cursor.close()

    def _execute_query(self, query: str, params: Optional[List[Any]] = None) -> Any:
        """Execute SQL Server query (with mock support)"""
        # Mock results for testing
        if not self._connection and ';mock=true' in self.connection_string.lower():
            query_upper = query.upper()
            if 'SALES.SALESORDERHEADER' in query_upper:
                return [
                    {"SalesOrderID": 43659, "OrderDate": "2024-05-01", "CustomerID": 29825, "TotalDue": 23153.23, "Status": 5},
                    {"SalesOrderID": 43660, "OrderDate": "2024-05-01", "CustomerID": 29672, "TotalDue": 1457.33, "Status": 5},
                    {"SalesOrderID": 43661, "OrderDate": "2024-05-01", "CustomerID": 29734, "TotalDue": 36865.80, "Status": 5},
                    {"SalesOrderID": 43662, "OrderDate": "2024-05-02", "CustomerID": 29993, "TotalDue": 32474.93, "Status": 4},
                    {"SalesOrderID": 43663, "OrderDate": "2024-05-02", "CustomerID": 29565, "TotalDue": 472.31, "Status": 5},
                ]
            if 'SALESLT.CUSTOMER' in query_upper:
                return [
                    {"CustomerID": 29825, "FirstName": "James", "LastName": "Kramer", "EmailAddress": "james@example.com"},
                    {"CustomerID": 29672, "FirstName": "Linda", "LastName": "Nixon", "EmailAddress": "linda@example.com"},
                    {"CustomerID": 29734, "FirstName": "Robert", "LastName": "Vane", "EmailAddress": "robert@example.com"},
                ]
            return [{"mock_col": "mock_val"}]

        with self._get_cursor() as cursor:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            # Return results for SELECT
            if query.strip().upper().startswith('SELECT'):
                # Fetch as list of dicts for consistency
                columns = [column[0] for column in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
            # Return row count for others
            else:
                return cursor.rowcount

    def list_tables(self) -> List[str]:
        """List tables in SQL Server database"""
        if not self._connected:
            raise ConnectionError("Not connected to database")

        query = """
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_TYPE = 'BASE TABLE' 
            AND TABLE_SCHEMA NOT IN ('sys', 'information_schema')
            ORDER BY TABLE_NAME
        """
        results = self._execute_query(query)
        return [row['TABLE_NAME'] for row in results]

    def get_table_schema(self, table_name: str) -> List[Dict[str, Any]]:
        """Get schema for a SQL Server table"""
        if not self._connected:
            raise ConnectionError("Not connected to database")

        query = """
            SELECT 
                COLUMN_NAME, 
                DATA_TYPE, 
                IS_NULLABLE,
                COLUMN_DEFAULT
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = ?
            ORDER BY ORDINAL_POSITION
        """
        results = self._execute_query(query, params=[table_name])
        
        schema = []
        for row in results:
            schema.append({
                'name': row['COLUMN_NAME'],
                'type': row['DATA_TYPE'],
                'nullable': row['IS_NULLABLE'] == 'YES',
                'default': row['COLUMN_DEFAULT']
            })
        return schema
