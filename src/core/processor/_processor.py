"""
Enhanced Processor Module

Main integration point for data processing that combines:
- DuckDB connection management
- Plugin system integration
- Configuration-driven behavior
- All data connectors (CSV, PostgreSQL, MySQL, API)
- Streaming support for large datasets
- Backward compatibility with data-processor.py
"""

import logging
from typing import Optional, Dict, Any, List, Union, Callable
from pathlib import Path
import threading
import time

import duckdb
import pandas as pd

from ..plugins import PluginRegistry, Plugin
from ..config.loader import Config
from ..database import DatabaseConnection
from ..connectors import CSVConnector, get_connector, CONNECTOR_REGISTRY
from ..connectors.excel import ExcelConnector
from ..connectors.json import JSONConnector
from .streaming import StreamProcessor
from .query import QueryExecutor
from .export import DataExporter


logger = logging.getLogger(__name__)


class Processor:
    """
    Enhanced Processor class for DuckDB data processing

    Features:
    - Configuration-driven behavior
    - Plugin system integration
    - Multiple data connectors (CSV, PostgreSQL, MySQL, API)
    - Streaming support for large datasets
    - Query execution with caching
    - Multiple export formats
    - Backward compatible with data-processor.py
    """

    def __init__(
        self,
        config: Optional[Config] = None,
        config_path: Optional[str] = None,
        connection: Optional[duckdb.DuckDBPyConnection] = None,
        plugin_registry: Optional[PluginRegistry] = None,
        max_memory_mb: Optional[int] = None,
        streaming_threshold_mb: Optional[int] = None,
        cache_enabled: bool = True,
        track_queries: bool = False,
    ):
        """
        Initialize Processor

        Args:
            config: Config object (optional)
            config_path: Path to config file (optional)
            connection: Existing DuckDB connection (optional)
            plugin_registry: Plugin registry instance (optional)
            max_memory_mb: Memory limit in MB (optional, default from config or 512)
            streaming_threshold_mb: Threshold for streaming in MB (optional, default from config or 100)
            cache_enabled: Enable query result caching (default True)
            track_queries: Enable query history tracking (default False)
        """
        # Load configuration
        if config:
            self._config = config
        elif config_path:
            self._config = Config(config_path)
            self._config.load()
        else:
            # Create default config
            self._config = self._create_default_config()

        # Initialize DuckDB connection
        if connection:
            self._connection = connection
            self._owns_connection = False
        else:
            self._connection = duckdb.connect(':memory:')
            self._owns_connection = True

        # Initialize components
        self._columns: List[str] = []
        self._table_name = 'data'
        self._cache: Dict[str, Any] = {}
        self._cache_enabled = cache_enabled
        self._query_history: List[Dict[str, Any]] = []
        self._track_queries = track_queries

        # Memory settings
        self._max_memory_mb = max_memory_mb or self._config.get('processor.max_memory_mb', 512)
        self._streaming_threshold_mb = streaming_threshold_mb or self._config.get('processor.streaming_threshold_mb', 100)

        # Initialize plugin registry
        if plugin_registry:
            self._plugin_registry = plugin_registry
        else:
            plugin_search_paths = self._config.get('processor.plugins.search_paths', [])
            self._plugin_registry = PluginRegistry(search_paths=plugin_search_paths)

            # Auto-load plugins if configured
            if self._config.get('processor.plugins.auto_load', False):
                self._plugin_registry.load_plugins()

        # Initialize stream processor
        self._stream_processor: Optional[StreamProcessor] = None

        # Initialize query executor
        self._query_executor = QueryExecutor(
            connection=self._connection,
            cache_enabled=cache_enabled,
            track_queries=track_queries
        )

        # Initialize data exporter
        self._exporter = DataExporter(
            connection=self._connection,
            config=self._config
        )

        # Initialize connector registry reference
        self._connectors: Dict[str, Any] = {}

        # Call plugin hook
        self._call_plugin_hook('on_processor_load', self)

        logger.info("Processor initialized successfully")

    def _create_default_config(self) -> Config:
        """Create default configuration"""
        mock_config = Mock()
        mock_config.processor = Mock()
        mock_config.processor.default_connector = "csv"
        mock_config.processor.max_memory_mb = 512
        mock_config.processor.streaming_threshold_mb = 100
        mock_config.processor.plugins = Mock()
        mock_config.processor.plugins.enabled = True
        mock_config.processor.plugins.auto_load = False
        mock_config.processor.export = Mock()
        mock_config.processor.export.default_format = "csv"
        mock_config.processor.export.include_headers = True
        mock_config.get = lambda key, default=None: default
        return mock_config

    @property
    def config(self) -> Config:
        """Get configuration"""
        return self._config

    @property
    def connection(self) -> duckdb.DuckDBPyConnection:
        """Get DuckDB connection"""
        return self._connection

    @property
    def columns(self) -> List[str]:
        """Get column names"""
        return self._columns.copy()

    @property
    def table_name(self) -> str:
        """Get current table name"""
        return self._table_name

    @property
    def plugin_registry(self) -> PluginRegistry:
        """Get plugin registry"""
        return self._plugin_registry

    # ========================================================================
    #  Data Loading Methods
    # ========================================================================

    def load_csv(
        self,
        csv_path: str,
        table_name: Optional[str] = None,
        delimiter: str = ',',
        has_header: bool = True,
        encoding: str = 'utf-8',
    ) -> pd.DataFrame:
        """
        Load CSV file into processor

        Args:
            csv_path: Path to CSV file
            table_name: Target table name (optional, default 'data')
            delimiter: CSV delimiter (default ',')
            has_header: Whether CSV has header row (default True)
            encoding: File encoding (default 'utf-8')

        Returns:
            DataFrame with loaded data

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is empty or invalid
        """
        # Validate file exists
        path = Path(csv_path)
        if not path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")

        # Create CSV connector
        connector = CSVConnector(
            delimiter=delimiter,
            has_header=has_header,
            encoding=encoding
        )

        # Get file size for streaming decision
        file_size = path.stat().st_size
        streaming_threshold = self._streaming_threshold_mb * 1024 * 1024

        # Use streaming for large files
        if file_size > streaming_threshold:
            return self._load_csv_streaming(connector, csv_path, table_name)
        else:
            return self._load_csv_direct(connector, csv_path, table_name)

    def _load_csv_direct(
        self,
        connector: CSVConnector,
        csv_path: str,
        table_name: Optional[str] = None,
    ) -> pd.DataFrame:
        """Load CSV directly into memory"""
        target_table = table_name or 'data'
        self._table_name = target_table

        # Read CSV data
        rows = list(connector.read_csv(csv_path))

        if not rows:
            raise ValueError(f"Empty CSV file: {csv_path}")

        # Infer schema and create table
        self._columns = list(rows[0].keys())

        # Create table
        self._create_table_from_rows(rows, target_table)

        # Insert data
        self._insert_rows(rows, target_table)

        # Call plugin hook
        self._call_plugin_hook('on_data_load', rows)

        logger.info(f"Loaded {len(rows)} rows from {csv_path} into table {target_table}")

        return self.sql(f'SELECT * FROM {self._table_name}')

    def _load_csv_streaming(
        self,
        connector: CSVConnector,
        csv_path: str,
        table_name: Optional[str] = None,
    ) -> pd.DataFrame:
        """Load CSV using streaming for large files"""
        target_table = table_name or 'data'
        self._table_name = target_table

        # Initialize streaming
        total_rows = 0
        first_chunk = True

        for chunk in connector.stream_csv(csv_path):
            if first_chunk:
                # Create table from first chunk
                self._columns = list(chunk[0].keys())
                self._create_table_from_rows(chunk, target_table)
                first_chunk = False

            # Insert chunk
            self._insert_rows(chunk, target_table)
            total_rows += len(chunk)

        # Call plugin hook
        self._call_plugin_hook('on_data_load', {'rows_loaded': total_rows})

        logger.info(f"Streamed {total_rows} rows from {csv_path} into table {target_table}")

        return self.sql(f'SELECT * FROM {self._table_name}')

    def load_excel(
        self,
        excel_path: str,
        table_name: Optional[str] = None,
        sheet_name: Optional[str] = None,
        header_row: int = 0,
    ) -> pd.DataFrame:
        """
        Load Excel file into processor

        Args:
            excel_path: Path to Excel file
            table_name: Target table name (optional, default 'data')
            sheet_name: Sheet name to load (default: first sheet)
            header_row: Row number containing headers (0-indexed, default 0)

        Returns:
            DataFrame with loaded data

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is empty or invalid
        """
        # Validate file exists
        path = Path(excel_path)
        if not path.exists():
            raise FileNotFoundError(f"Excel file not found: {excel_path}")

        # Create Excel connector
        connector = ExcelConnector(
            sheet_name=sheet_name,
            header_row=header_row
        )

        # Load data using connector
        target_table = table_name or 'data'
        self._table_name = target_table

        # Read Excel data
        rows = list(connector.read(excel_path))

        if not rows:
            raise ValueError(f"Empty Excel file: {excel_path}")

        # Infer schema and create table
        self._columns = list(rows[0].keys())

        # Create table
        self._create_table_from_rows(rows, target_table)

        # Insert data
        self._insert_rows(rows, target_table)

        # Call plugin hook
        self._call_plugin_hook('on_data_load', rows)

        logger.info(f"Loaded {len(rows)} rows from {excel_path} into table {target_table}")

        return self.sql(f'SELECT * FROM {target_table}')

    def load_json(
        self,
        json_path: str,
        table_name: Optional[str] = None,
        format: str = 'json',
    ) -> pd.DataFrame:
        """
        Load JSON or JSONL file into processor

        Args:
            json_path: Path to JSON file
            table_name: Target table name (optional, default 'data')
            format: File format ('json' or 'jsonl', default 'json')

        Returns:
            DataFrame with loaded data

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is empty or invalid
        """
        # Validate file exists
        path = Path(json_path)
        if not path.exists():
            raise FileNotFoundError(f"JSON file not found: {json_path}")

        # Create JSON connector
        connector = JSONConnector()

        # Load data using connector
        target_table = table_name or 'data'
        self._table_name = target_table

        # Read JSON data
        rows = list(connector.read(json_path, format=format))

        if not rows:
            raise ValueError(f"Empty JSON file: {json_path}")

        # Infer schema and create table
        self._columns = list(rows[0].keys())

        # Create table
        self._create_table_from_rows(rows, target_table)

        # Insert data
        self._insert_rows(rows, target_table)

        # Call plugin hook
        self._call_plugin_hook('on_data_load', rows)

        logger.info(f"Loaded {len(rows)} rows from {json_path} into table {target_table}")

        return self.sql(f'SELECT * FROM {self._table_name}')

    def load_database(
        self,
        connection_string: str,
        query: str,
        table_name: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Load data from database query

        Args:
            connection_string: Database connection string (postgresql:// or mysql://)
            query: SQL query to execute
            table_name: Target table name (optional)

        Returns:
            DataFrame with loaded data

        Raises:
            ValueError: If database type is not supported
            ConnectionError: If database connection fails
        """
        # Detect database type from connection string
        conn_lower = connection_string.lower()
        if conn_lower.startswith(('postgresql://', 'postgres://')):
            from ..connectors.postgresql import PostgreSQLConnector
            connector = PostgreSQLConnector(connection_string)
        elif conn_lower.startswith('mysql://'):
            from ..connectors.mysql import MySQLConnector
            connector = MySQLConnector(connection_string)
        elif conn_lower.startswith(('mssql://', 'mssql+pyodbc://', 'sqlserver://')) or 'driver=' in conn_lower:
            from ..connectors.mssql import MSSQLConnector
            connector = MSSQLConnector(connection_string)
        else:
            raise ValueError(
                f"Unsupported database type. Supported: postgresql://, mysql://, mssql://\n"
                f"Got: {connection_string[:20]}..."
            )

        # Connect to database
        try:
            connector.connect()
        except Exception as e:
            raise ConnectionError(f"Failed to connect to database: {e}")

        # Set target table
        target_table = table_name or 'data'
        self._table_name = target_table

        # Read data from database
        try:
            rows = list(connector.read(query=query))
        except Exception as e:
            connector.disconnect()
            raise ValueError(f"Failed to execute query: {e}")

        # Clean up connection
        connector.disconnect()

        if not rows:
            raise ValueError(f"Query returned no results: {query}")

        # Create table and insert data
        self._create_table_from_rows(rows, target_table)
        self._insert_rows(rows, target_table)

        # Call plugin hook
        self._call_plugin_hook('on_data_load', rows)

        logger.info(f"Loaded {len(rows)} rows from database into table {target_table}")

        return self.sql(f'SELECT * FROM {self._table_name}')

    def load_parquet(
        self,
        parquet_path: str,
        table_name: Optional[str] = None,
        columns: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Load data from Parquet file.

        Args:
            parquet_path: Path to Parquet file
            table_name: Target table name (optional)
            columns: Optional list of columns to read (column pruning)

        Returns:
            DataFrame with loaded data

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is not valid Parquet
        """
        from ..connectors.parquet import ParquetConnector

        # Create connector
        connector = ParquetConnector(columns=columns)

        # Validate file
        connector.validate(parquet_path)

        # Set target table
        target_table = table_name or 'data'
        self._table_name = target_table

        # Read data from Parquet
        rows = list(connector.read(parquet_path))

        if not rows:
            raise ValueError(f"Empty Parquet file: {parquet_path}")

        # Infer schema and create table
        self._columns = list(rows[0].keys())

        # Create table
        self._create_table_from_rows(rows, target_table)

        # Insert data
        self._insert_rows(rows, target_table)

        # Call plugin hook
        self._call_plugin_hook('on_data_load', rows)

        logger.info(f"Loaded {len(rows)} rows from {parquet_path} into table {target_table}")

        return self.sql(f'SELECT * FROM {self._table_name}')

    def load_api(
        self,
        api_url: str,
        table_name: Optional[str] = None,
        auth_type: Optional[str] = None,
        token: Optional[str] = None,
        api_key: Optional[str] = None,
        api_key_header: str = 'X-API-Key',
        headers: Optional[Dict[str, str]] = None,
        method: str = 'GET',
        params: Optional[Dict[str, Any]] = None,
        data_path: Optional[str] = None,
        pagination: Optional[str] = None,
        max_pages: Optional[int] = None,
        **kwargs
    ) -> pd.DataFrame:
        """
        Load data from API endpoint

        @MX:NOTE: Supports REST API data ingestion with authentication and pagination.

        Args:
            api_url: API endpoint URL
            table_name: Target table name (optional, default 'data')
            auth_type: Authentication type ('bearer', 'api_key', 'basic', None)
            token: Bearer token for bearer auth
            api_key: API key value
            api_key_header: Header name for API key (default: 'X-API-Key')
            headers: Additional HTTP headers
            method: HTTP method (default: 'GET')
            params: Query parameters
            data_path: JSONPath to extract data array (e.g., 'data.items')
            pagination: Pagination type ('cursor', 'offset', 'link', None)
            max_pages: Maximum number of pages to fetch
            **kwargs: Additional API connector parameters

        Returns:
            DataFrame with loaded data

        Raises:
            ImportError: If requests library is not installed
            ValueError: If URL is invalid
            requests.RequestException: If API request fails

        Example:
            >>> # Bearer token authentication
            >>> processor.load_api('https://api.example.com/users',
            ...                    auth_type='bearer', token='xxx')
            >>>
            >>> # API key authentication
            >>> processor.load_api('https://api.example.com/data',
            ...                    auth_type='api_key', api_key='xxx')
        """
        from ..connectors.api import APIConnector

        # Set target table
        target_table = table_name or 'data'
        self._table_name = target_table

        # Create API connector
        connector = APIConnector(
            auth_type=auth_type,
            token=token,
            api_key=api_key,
            api_key_header=api_key_header,
            headers=headers,
            **kwargs
        )

        # Validate URL
        connector.validate(api_url)

        # Connect and fetch data
        connector.connect()

        try:
            rows = list(connector.read(
                url=api_url,
                method=method,
                params=params,
                data_path=data_path,
                pagination=pagination,
                max_pages=max_pages
            ))
        finally:
            connector.disconnect()

        if not rows:
            raise ValueError(f"API returned no data: {api_url}")

        # Create table and insert data
        self._create_table_from_rows(rows, target_table)
        self._insert_rows(rows, target_table)

        # Call plugin hook
        self._call_plugin_hook('on_data_load', rows)

        logger.info(f"Loaded {len(rows)} rows from API {api_url} into table {target_table}")

        return self.sql(f'SELECT * FROM {self._table_name}')

    def load_web(
        self,
        url: str,
        table_name: Optional[str] = None,
        selector: str = 'table',
        extract_mode: str = 'table',
        headers: Optional[Dict[str, str]] = None,
    ) -> pd.DataFrame:
        """
        Load data from a web page by scraping HTML content.

        Args:
            url: Web page URL to scrape
            table_name: Target table name (optional, default 'data')
            selector: CSS selector to target elements (default 'table')
            extract_mode: Extraction mode ('table', 'css', 'xpath')
            headers: Custom HTTP headers

        Returns:
            DataFrame with loaded data
        """
        from ..connectors.web import WebConnector

        target_table = table_name or 'data'
        self._table_name = target_table

        connector = WebConnector(headers=headers)
        connector.validate(url)
        connector.connect()

        try:
            rows = list(connector.read(
                url=url,
                selector=selector,
                extract_mode=extract_mode,
            ))
        finally:
            connector.disconnect()

        if not rows:
            raise ValueError(f"No data extracted from {url}")

        self._columns = list(rows[0].keys())
        self._create_table_from_rows(rows, target_table)
        self._insert_rows(rows, target_table)

        self._call_plugin_hook('on_data_load', rows)

        logger.info(f"Loaded {len(rows)} rows from web {url} into table {target_table}")

        return self.sql(f'SELECT * FROM {self._table_name}')

    def load_df(
        self,
        df: pd.DataFrame,
        table_name: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Load pandas DataFrame directly into processor

        @MX:NOTE: [AUTO] Useful for testing and in-memory operations. Converts DataFrame to DuckDB table.

        Args:
            df: pandas DataFrame to load
            table_name: Target table name (optional, default 'data')

        Returns:
            DataFrame with loaded data (preview)

        Raises:
            ValueError: If DataFrame is empty
        """
        if df.empty:
            raise ValueError("Cannot load empty DataFrame")

        # Set target table
        target_table = table_name or 'data'
        self._table_name = target_table

        # Convert DataFrame to list of dicts (rows)
        rows = df.to_dict('records')

        # Convert NaN values to None for SQL compatibility
        for row in rows:
            for key, value in list(row.items()):
                if pd.isna(value):
                    row[key] = None
                elif isinstance(value, (pd.Timestamp)):
                    row[key] = str(value)

        # Create table and insert data
        self._create_table_from_rows(rows, target_table)
        self._insert_rows(rows, target_table)

        # Call plugin hook
        self._call_plugin_hook('on_data_load', rows)

        logger.info(f"Loaded {len(rows)} rows from DataFrame into table {target_table}")

        return self.sql(f'SELECT * FROM {self._table_name}')

    # ========================================================================
    #  Table Management Methods
    # ========================================================================

    def _create_table_from_rows(self, rows: List[Dict], table_name: str) -> None:
        """Create DuckDB table from row data with type inference"""
        if not rows:
            return

        # Get all unique columns
        all_columns = set()
        for row in rows:
            all_columns.update(row.keys())

        self._columns = list(all_columns)

        # Infer data types for each column
        column_types = {}
        for col in self._columns:
            # Find first non-null value to infer type
            for row in rows:
                value = row.get(col)
                if value is not None:
                    # Infer type from value
                    if isinstance(value, bool):
                        column_types[col] = 'BOOLEAN'
                    elif isinstance(value, int):
                        column_types[col] = 'INTEGER'
                    elif isinstance(value, float):
                        column_types[col] = 'DOUBLE'
                    elif isinstance(value, (pd.Timestamp)):
                        column_types[col] = 'TIMESTAMP'
                    else:
                        column_types[col] = 'VARCHAR'
                    break
            # If all values are null, default to VARCHAR
            if col not in column_types:
                column_types[col] = 'VARCHAR'

        # Build CREATE TABLE statement
        column_defs = ', '.join(f'"{col}" {column_types[col]}' for col in self._columns)

        # Only add _row column if it doesn't already exist
        if '_row' not in self._columns:
            column_defs += ', _row INTEGER'

        self._connection.execute(f'DROP TABLE IF EXISTS {table_name}')
        self._connection.execute(f'CREATE TABLE {table_name} ({column_defs})')

    def _insert_rows(self, rows: List[Dict], table_name: str) -> None:
        """Insert rows into table, preserving data types"""
        if not rows:
            return

        # Check if _row column already exists in data
        has_row_column = '_row' in self._columns

        # Build INSERT statement
        col_list = ', '.join(f'"{col}"' for col in self._columns)
        placeholders = ', '.join(['?'] * len(self._columns))

        # Add _row column only if it doesn't exist in data
        if not has_row_column:
            col_list += ', _row'
            placeholders += ', ?'

        for i, row in enumerate(rows):
            # Preserve original data types instead of converting to string
            values = []
            for col in self._columns:
                value = row.get(col)
                if value == '' or value is None:
                    values.append(None)
                else:
                    values.append(value)
            if not has_row_column:
                values.append(i)
            self._connection.execute(
                f'INSERT INTO {table_name} ({col_list}) VALUES ({placeholders})',
                values
            )

    # ========================================================================
    #  Query Methods (Backward Compatible)
    # ========================================================================

    def sql(self, query: str, parameters: Optional[List] = None) -> pd.DataFrame:
        """
        Execute SQL query

        Args:
            query: SQL query to execute
            parameters: Query parameters (optional)

        Returns:
            DataFrame with query results
        """
        return self._query_executor.execute(query, parameters)

    def preview(self, n: int = 10) -> pd.DataFrame:
        """
        Show first n rows

        Args:
            n: Number of rows to show (default 10)

        Returns:
            DataFrame with preview data
        """
        return self.sql(f'SELECT * FROM {self._table_name} LIMIT {n}')

    def schema(self) -> pd.DataFrame:
        """
        Show table schema

        Returns:
            DataFrame with schema information
        """
        return self.sql(f'DESCRIBE {self._table_name}')

    def coverage(self) -> pd.DataFrame:
        """
        Calculate column coverage (non-null percentage)

        Returns:
            DataFrame with coverage information
        """
        total = self._connection.execute(
            f'SELECT COUNT(*) FROM {self._table_name}'
        ).fetchone()[0]

        rows = []
        for col in self._columns:
            count = self._connection.execute(
                f'SELECT COUNT(*) FROM {self._table_name} WHERE "{col}" IS NOT NULL AND "{col}" != \'\''
            ).fetchone()[0]
            rows.append({
                'column': col,
                'present': count,
                'coverage_%': round(count / total * 100, 1) if total else 0
            })

        return pd.DataFrame(rows)

    # ========================================================================
    #  Data Processing Methods (Backward Compatible)
    # ========================================================================

    def filter(self, where: str) -> pd.DataFrame:
        """
        Filter rows based on condition

        Args:
            where: WHERE clause condition

        Returns:
            DataFrame with filtered rows
        """
        return self.sql(f'SELECT * FROM {self._table_name} WHERE {where}')

    def create_view(self, name: str, where: str) -> None:
        """
        Create a filtered view

        Args:
            name: View name
            where: WHERE clause condition
        """
        self._connection.execute(
            f'CREATE OR REPLACE VIEW {name} AS '
            f'SELECT * FROM {self._table_name} WHERE {where}'
        )
        logger.info(f"View '{name}' created")

    def add_column(self, new_col: str, expr: str, source: Optional[str] = None) -> None:
        """
        Add a derived column

        Args:
            new_col: New column name
            expr: SQL expression for column value
            source: Source table/view (optional)
        """
        tbl = source or self._table_name

        # Check if column exists and drop it
        existing = [r[0] for r in self._connection.execute(f'DESCRIBE {tbl}').fetchall()]
        if new_col in existing:
            self._connection.execute(f'ALTER TABLE {tbl} DROP COLUMN "{new_col}"')

        # Add column
        self._connection.execute(f'ALTER TABLE {tbl} ADD COLUMN "{new_col}" VARCHAR')
        self._connection.execute(f'UPDATE {tbl} SET "{new_col}" = CAST(({expr}) AS VARCHAR)')
        self._columns.append(new_col)

        logger.info(f"Column '{new_col}' added")

    def aggregate(
        self,
        group_by: Union[str, List[str]],
        agg_field: str,
        func: str = 'SUM',
        source: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Group-by aggregation

        Args:
            group_by: Column(s) to group by
            agg_field: Column to aggregate
            func: Aggregation function (default 'SUM')
            source: Source table/view (optional)

        Returns:
            DataFrame with aggregated results
        """
        tbl = source or self._table_name

        if isinstance(group_by, list):
            gb = ', '.join(f'"{c}"' for c in group_by)
        else:
            gb = f'"{group_by}"'

        return self.sql(f"""
            SELECT {gb},
                   COUNT(*)                                      AS count,
                   ROUND({func}(TRY_CAST("{agg_field}" AS DOUBLE)), 2) AS {func.lower()}_{agg_field}
            FROM {tbl}
            WHERE "{agg_field}" IS NOT NULL AND "{agg_field}" != ''
            GROUP BY {gb}
            ORDER BY {func.lower()}_{agg_field} DESC
        """)

    def pivot(
        self,
        row_key: str,
        col_key: str,
        val: str,
        func: str = 'SUM',
        source: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Cross-tab two categorical keys

        Args:
            row_key: Row key column
            col_key: Column key column
            val: Value column
            func: Aggregation function (default 'SUM')
            source: Source table/view (optional)

        Returns:
            DataFrame with pivoted results
        """
        tbl = source or self._table_name

        # Get distinct column values
        col_vals = self._connection.execute(
            f'SELECT DISTINCT "{col_key}" FROM {tbl} '
            f'WHERE "{col_key}" IS NOT NULL ORDER BY "{col_key}"'
        ).fetchall()
        col_vals = [r[0] for r in col_vals]

        # Build CASE expressions
        cases = ', '.join(
            f"ROUND({func}(CASE WHEN \"{col_key}\" = '{v}' "
            f"THEN TRY_CAST(\"{val}\" AS DOUBLE) END), 2) AS \"{v}\""
            for v in col_vals
        )

        return self.sql(f"""
            SELECT "{row_key}", {cases}
            FROM {tbl}
            GROUP BY "{row_key}"
            ORDER BY "{row_key}"
        """)

    def group_by(
        self,
        group_columns: List[str],
        agg_column: str,
        func: str = 'SUM',
        source: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Group by specified columns and perform aggregation.

        Args:
            group_columns: List of columns to group by
            agg_column: Column to aggregate
            func: Aggregation function (SUM, AVG, MIN, MAX, COUNT)
            source: Source table/view (optional)

        Returns:
            DataFrame with grouped results

        Example:
            >>> processor.group_by(['category'], 'value', 'SUM')
            >>> processor.group_by(['category', 'region'], 'sales', 'AVG')
        """
        tbl = source or self._table_name
        gb = ', '.join([f'"{col}"' for col in group_columns])

        func_map = {
            'SUM': 'SUM',
            'AVG': 'AVG',
            'MEAN': 'AVG',
            'MIN': 'MIN',
            'MAX': 'MAX',
            'COUNT': 'COUNT',
            'STD': 'STDDEV',
            'VAR': 'VARIANCE'
        }

        sql_func = func_map.get(func.upper(), func)

        return self.sql(f"""
            SELECT {gb},
                   {sql_func}(TRY_CAST("{agg_column}" AS DOUBLE)) AS {sql_func.lower()}_{agg_column}
            FROM {tbl}
            GROUP BY {gb}
            ORDER BY {sql_func.lower()}_{agg_column} DESC
        """)

    def merge(
        self,
        other_table: str,
        on: List[str],
        how: str = 'inner',
        source: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Merge/join with another table.

        Args:
            other_table: Name of table to join with
            on: List of column names to join on
            how: Join type (inner, left, right, outer, cross)
            source: Source table (optional)

        Returns:
            DataFrame with joined results

        Example:
            >>> processor.merge('other_table', ['id'], 'left')
            >>> processor.merge('customers', ['customer_id'], 'inner')
        """
        tbl = source or self._table_name

        # Map join type to SQL syntax
        join_map = {
            'inner': 'INNER JOIN',
            'left': 'LEFT JOIN',
            'right': 'RIGHT JOIN',
            'outer': 'FULL OUTER JOIN',
            'full': 'FULL OUTER JOIN',
            'cross': 'CROSS JOIN'
        }
        join_sql = join_map.get(how.lower(), f'{how.upper()} JOIN')

        # For CROSS JOIN, no ON clause
        if how.lower() == 'cross':
            return self.sql(f"""
                SELECT t1.*, t2.*
                FROM {tbl} AS t1
                {join_sql} {other_table} AS t2
            """)

        # Build join conditions with explicit aliases
        join_cols = ', '.join([f't1."{col}" = t2."{col}"' for col in on])

        # Select all columns from t1 and non-join columns from t2 to avoid duplicates
        return self.sql(f"""
            SELECT t1.*, t2.*
            FROM {tbl} AS t1
            {join_sql} {other_table} AS t2
            ON {join_cols}
        """)

    def window(
        self,
        func: str,
        over_column: str,
        partition_by: Optional[List[str]] = None,
        window_frame: Optional[str] = None,
        alias: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Apply window function for rolling analytics.

        Args:
            func: Window function (ROW_NUMBER, RANK, DENSE_RANK, LAG, LEAD,
                   SUM/AVG/MIN/MAX over, FIRST_VALUE, LAST_VALUE)
            over_column: Column to compute function over
            partition_by: Optional list of columns to partition by
            window_frame: Optional window frame specification
            alias: Optional alias for the window column

        Returns:
            DataFrame with window function results

        Example:
            >>> processor.window('ROW_NUMBER', 'date', ['category'])
            >>> processor.window('SUM', 'sales', ['region'], alias='running_total')
        """
        tbl = self._table_name

        # Functions that don't take a column argument
        no_arg_funcs = {'ROW_NUMBER', 'RANK', 'DENSE_RANK'}

        func_upper = func.upper()
        if func_upper in no_arg_funcs:
            sql_func = f'{func_upper}()'
        else:
            func_map = {
                'LAG': 'LAG',
                'LEAD': 'LEAD',
                'SUM': 'SUM',
                'AVG': 'AVG',
                'MIN': 'MIN',
                'MAX': 'MAX',
                'FIRST_VALUE': 'FIRST_VALUE',
                'LAST_VALUE': 'LAST_VALUE',
                'COUNT': 'COUNT'
            }
            sql_func = func_map.get(func_upper, func)

        # Generate default alias
        func_lower = sql_func.lower().replace('()', '')
        col_alias = alias if alias else f'{func_lower}_{over_column}'

        if partition_by:
            pb = ', '.join([f'"{col}"' for col in partition_by])
            over_clause = f'PARTITION BY {pb} ORDER BY "{over_column}"'
        else:
            over_clause = f'ORDER BY "{over_column}"'

        # For functions that take a column argument
        if func_upper not in no_arg_funcs:
            window_expr = f'{sql_func}("{over_column}") OVER ({over_clause})'
        else:
            window_expr = f'{sql_func} OVER ({over_clause})'

        return self.sql(f"""
            SELECT *,
                   {window_expr} AS {col_alias}
            FROM {tbl}
        """)

    def rolling_aggregate(
        self,
        agg_column: str,
        func: str = 'SUM',
        window_size: int = 3,
        order_by: Optional[str] = None,
        partition_by: Optional[List[str]] = None,
        source: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Apply rolling window aggregation.

        Args:
            agg_column: Column to aggregate
            func: Aggregation function (SUM, AVG, MIN, MAX, COUNT)
            window_size: Number of rows in rolling window
            order_by: Column to order by
            partition_by: Optional list of columns to partition by
            source: Source table (optional)

        Returns:
            DataFrame with rolling aggregation results
        """
        tbl = source or self._table_name

        func_map = {
            'SUM': 'SUM',
            'AVG': 'AVG',
            'MEAN': 'AVG',
            'MIN': 'MIN',
            'MAX': 'MAX',
            'COUNT': 'COUNT',
            'STD': 'STDDEV'
        }

        sql_func = func_map.get(func.upper(), func)
        order_col = order_by or agg_column

        window_frame = f'ROWS BETWEEN {window_size - 1} PRECEDING AND CURRENT ROW'

        if partition_by:
            pb = ', '.join([f'"{col}"' for col in partition_by])
            over_clause = f'PARTITION BY {pb} ORDER BY "{order_col}" {window_frame}'
        else:
            over_clause = f'ORDER BY "{order_col}" {window_frame}'

        return self.sql(f"""
            SELECT *,
                   {sql_func}("{agg_column}") OVER ({over_clause}) AS rolling_{sql_func.lower()}_{agg_column}
            FROM {tbl}
            ORDER BY "{order_col}"
        """)

    # ========================================================================
    #  Export Methods (Backward Compatible)
    # ========================================================================

    def export_csv(self, path: str, query: Optional[str] = None) -> None:
        """
        Export to CSV file

        Args:
            path: Output file path
            query: SQL query (optional, exports full table if not provided)
        """
        q = query or f'SELECT * FROM {self._table_name}'
        self._connection.execute(f"COPY ({q}) TO '{path}' (HEADER, DELIMITER ',')")
        logger.info(f"Exported to {path}")

    def export_json(self, path: str, query: Optional[str] = None) -> None:
        """
        Export to JSON file

        Args:
            path: Output file path
            query: SQL query (optional)
        """
        q = query or f'SELECT * FROM {self._table_name}'
        rows = self._connection.execute(q).df().to_dict(orient='records')
        Path(path).write_text(json.dumps(rows, indent=2, default=str))
        logger.info(f"Exported to {path}")

    def export_parquet(self, path: str, query: Optional[str] = None) -> None:
        """
        Export to Parquet file

        Args:
            path: Output file path
            query: SQL query (optional)
        """
        q = query or f'SELECT * FROM {self._table_name}'
        self._connection.execute(f"COPY ({q}) TO '{path}' (FORMAT PARQUET)")
        logger.info(f"Exported to {path}")

    # ========================================================================
    #  Streaming Methods
    # ========================================================================

    def stream_query(
        self,
        query: str,
        parameters: Optional[List] = None,
        chunk_size: int = 10000,
    ):
        """
        Stream query results for large datasets

        Args:
            query: SQL query to execute
            parameters: Query parameters (optional)
            chunk_size: Rows per chunk (default 10000)

        Yields:
            List of dictionaries (chunks)
        """
        if not self._stream_processor:
            # Create database connection wrapper for streaming
            db_connection = DatabaseConnection(':memory:')
            db_connection._connection = self._connection

            self._stream_processor = StreamProcessor(
                db_connection=db_connection,
                memory_limit_mb=self._max_memory_mb,
                chunk_size=chunk_size
            )

        yield from self._stream_processor.stream_query(query, parameters)

    def pause_stream(self) -> None:
        """Pause streaming operation"""
        if self._stream_processor:
            self._stream_processor.pause()

    def resume_stream(self) -> None:
        """Resume paused streaming"""
        if self._stream_processor:
            self._stream_processor.resume()

    def cancel_stream(self) -> None:
        """Cancel streaming operation"""
        if self._stream_processor:
            self._stream_processor.cancel()

    @property
    def is_stream_paused(self) -> bool:
        """Check if stream is paused"""
        if self._stream_processor:
            from .streaming import StreamingState
            return self._stream_processor.state == StreamingState.PAUSED
        return False

    @property
    def is_stream_cancelled(self) -> bool:
        """Check if stream is cancelled"""
        if self._stream_processor:
            from .streaming import StreamingState
            return self._stream_processor.state == StreamingState.CANCELLED
        return False

    # ========================================================================
    #  Plugin Integration Methods
    # ========================================================================

    def _call_plugin_hook(self, hook_name: str, *args, **kwargs) -> None:
        """
        Call plugin hook on all enabled plugins

        Args:
            hook_name: Name of hook method to call
            *args: Positional arguments
            **kwargs: Keyword arguments
        """
        if not self._config.get('processor.plugins.enabled', False):
            return

        for plugin in self._plugin_registry.get_enabled_plugins():
            try:
                hook_method = getattr(plugin, hook_name, None)
                if hook_method and callable(hook_method):
                    hook_method(*args, **kwargs)
            except Exception as e:
                logger.warning(f"Plugin {plugin.name} hook {hook_name} failed: {e}")

    def register_plugin(self, plugin: Plugin) -> None:
        """
        Register a plugin with processor

        Args:
            plugin: Plugin instance to register
        """
        self._plugin_registry.register(plugin)
        self._plugin_registry.enable_plugin(plugin.name)

    # ========================================================================
    #  Statistics and Metadata Methods
    # ========================================================================

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about loaded data

        Returns:
            Dictionary with row count, column count, and other stats
        """
        row_count = self._connection.execute(
            f'SELECT COUNT(*) FROM {self._table_name}'
        ).fetchone()[0]

        return {
            'row_count': row_count,
            'column_count': len(self._columns),
            'columns': self._columns,
            'table_name': self._table_name,
        }

    def get_query_history(self) -> List[Dict[str, Any]]:
        """
        Get query execution history

        Returns:
            List of query records
        """
        return self._query_history.copy()

    def explain(self, query: str) -> Any:
        """
        Get query execution plan

        Args:
            query: SQL query to explain

        Returns:
            Execution plan
        """
        return self._connection.execute(f'EXPLAIN {query}').fetchall()

    # ========================================================================
    #  Context Manager Support
    # ========================================================================

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()

    def close(self) -> None:
        """Close and cleanup resources"""
        if self._owns_connection and self._connection:
            self._connection.close()
            self._connection = None

        # Clear cache
        self._cache.clear()

        logger.info("Processor closed")

    # ========================================================================
    #  Data Transformation Methods
    # ========================================================================

    def transform(self, column: Union[str, Dict[str, Callable]], func: Optional[Callable] = None) -> None:
        """
        Transform column(s) using Python lambda or function.

        Args:
            column: Column name to transform, or dict of {column: function}
            func: Python function to apply (when column is a single string)
        """
        if isinstance(column, dict):
            # Multiple column transformations
            for col, transformation_func in column.items():
                if col not in self._columns:
                    raise ValueError(f"Column '{col}' not found")
                # Apply transformation
                self._connection.execute(
                    f'ALTER TABLE {self._table_name} '
                    f'ADD COLUMN "{col}_new" VARCHAR'
                )
                # Get current values and apply transformation
                rows = self._connection.execute(f'SELECT _row, "{col}" FROM {self._table_name}').fetchall()
                transformed_rows = []
                for row in rows:
                    row_id, val = row
                    try:
                        new_val = transformation_func(val)
                        transformed_rows.append((row_id, new_val))
                    except Exception:
                        transformed_rows.append((row_id, val))

                # Update table with transformed values
                for row_id, new_val in transformed_rows:
                    self._connection.execute(
                        f'UPDATE {self._table_name} '
                        f'SET "{col}_new" = ? WHERE _row = ?',
                        [new_val, row_id]
                    )

                # Replace old column with transformed one
                self._connection.execute(
                    f'ALTER TABLE {self._table_name} DROP COLUMN "{col}"'
                )
                self._connection.execute(
                    f'ALTER TABLE {self._table_name} RENAME COLUMN "{col}_new" TO "{col}"'
                )
        else:
            # Single column transformation
            if column not in self._columns:
                raise ValueError(f"Column '{column}' not found")
            if func is None:
                raise ValueError("Function must be provided for single column transformation")

            # Apply transformation
            self._connection.execute(
                f'ALTER TABLE {self._table_name} ADD COLUMN "{column}_new" VARCHAR'
            )
            rows = self._connection.execute(f'SELECT _row, "{column}" FROM {self._table_name}').fetchall()
            transformed_rows = []
            for row in rows:
                row_id, val = row
                try:
                    new_val = func(val)
                    transformed_rows.append((row_id, new_val))
                except Exception:
                    transformed_rows.append((row_id, val))

            for row_id, new_val in transformed_rows:
                self._connection.execute(
                    f'UPDATE {self._table_name} SET "{column}_new" = ? WHERE _row = ?',
                    [new_val, row_id]
                )

            self._connection.execute(f'ALTER TABLE {self._table_name} DROP COLUMN "{column}"')
            self._connection.execute(
                f'ALTER TABLE {self._table_name} RENAME COLUMN "{column}_new" TO "{column}"'
            )

        logger.info(f"Transformation applied to {column}")

    # ========================================================================
    #  Join Methods
    # ========================================================================

    def join(
        self,
        right_table: str,
        on: str,
        how: str = 'INNER',
        suffix: str = '_right'
    ) -> pd.DataFrame:
        """
        Join with another table.

        Args:
            right_table: Table to join with (must be loaded in same DuckDB connection)
            on: Join condition (column name)
            how: Join type (INNER, LEFT, RIGHT, OUTER)
            suffix: Suffix for overlapping column names

        Returns:
            DataFrame with joined results
        """
        join_sql = {
            'INNER': 'INNER JOIN',
            'LEFT': 'LEFT JOIN',
            'RIGHT': 'RIGHT JOIN',
            'OUTER': 'FULL OUTER JOIN',
            'CROSS': 'CROSS JOIN'
        }

        join_type = join_sql.get(how.upper(), 'INNER JOIN')

        # Build join query
        query = f"""
            SELECT *
            FROM {self._table_name} l
            {join_type} {right_table} r
            ON l.{on} = r.{on}
        """

        result = self.sql(query)

        # Update working table to the joined result
        self._table_name = f'joined_{self._table_name}_{right_table}'
        self._connection.execute(f'CREATE OR REPLACE VIEW {self._table_name} AS {query}')
        self._columns = list(result.columns)

        logger.info(f"Joined with {right_table} on {on} ({how})")
        return result

    # ========================================================================
    #  Additional Export Methods
    # ========================================================================

    def export_duckdb(self, path: str, table_name: Optional[str] = None) -> None:
        """
        Export to DuckDB database file.

        Args:
            path: Output database file path
            table_name: Table name to use in export (optional)
        """
        tbl = table_name or self._table_name

        # Export current table to DuckDB file
        self._connection.execute(f"COPY {tbl} TO '{path}'")
        logger.info(f"Exported to DuckDB database: {path}")


# Import json for export_json
import json
from unittest.mock import Mock
