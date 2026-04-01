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

        return self.preview()

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

        return self.preview()

    def load_database(
        self,
        connection_string: str,
        query: str,
        table_name: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Load data from database query

        Args:
            connection_string: Database connection string
            query: SQL query to execute
            table_name: Target table name (optional)

        Returns:
            DataFrame with loaded data
        """
        # This would be implemented with database connectors
        # For now, raise NotImplementedError
        raise NotImplementedError("Database loading not yet implemented")

    def load_api(
        self,
        api_url: str,
        table_name: Optional[str] = None,
        **kwargs
    ) -> pd.DataFrame:
        """
        Load data from API endpoint

        Args:
            api_url: API endpoint URL
            table_name: Target table name (optional)
            **kwargs: Additional API parameters

        Returns:
            DataFrame with loaded data
        """
        # This would be implemented with API connector
        # For now, raise NotImplementedError
        raise NotImplementedError("API loading not yet implemented")

    # ========================================================================
    #  Table Management Methods
    # ========================================================================

    def _create_table_from_rows(self, rows: List[Dict], table_name: str) -> None:
        """Create DuckDB table from row data"""
        if not rows:
            return

        # Get all unique columns
        all_columns = set()
        for row in rows:
            all_columns.update(row.keys())

        self._columns = list(all_columns)

        # Build CREATE TABLE statement
        column_defs = ', '.join(f'"{col}" VARCHAR' for col in self._columns)
        column_defs += ', _row INTEGER'

        self._connection.execute(f'DROP TABLE IF EXISTS {table_name}')
        self._connection.execute(f'CREATE TABLE {table_name} ({column_defs})')

    def _insert_rows(self, rows: List[Dict], table_name: str) -> None:
        """Insert rows into table"""
        if not rows:
            return

        # Build INSERT statement
        col_list = ', '.join(f'"{col}"' for col in self._columns) + ', _row'
        placeholders = ', '.join(['?'] * (len(self._columns) + 1))

        for i, row in enumerate(rows):
            values = [str(row.get(col, '')) if row.get(col, '') != '' else None
                     for col in self._columns]
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
            from .processor.streaming import StreamingState
            return self._stream_processor.state == StreamingState.PAUSED
        return False

    @property
    def is_stream_cancelled(self) -> bool:
        """Check if stream is cancelled"""
        if self._stream_processor:
            from .processor.streaming import StreamingState
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


# Import json for export_json
import json
from unittest.mock import Mock
