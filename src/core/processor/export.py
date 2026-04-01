"""
Data Export Module

Provides data export functionality with:
- CSV export
- JSON export
- Parquet export
- DuckDB export
- Configuration-driven settings
"""

import logging
from typing import Optional, Dict, Any
from pathlib import Path
import json
import duckdb

logger = logging.getLogger(__name__)


class DataExporter:
    """
    Data exporter with multiple format support
    """

    def __init__(
        self,
        connection: duckdb.DuckDBPyConnection,
        config: Optional[Any] = None,
    ):
        """
        Initialize data exporter

        Args:
            connection: DuckDB connection
            config: Configuration object (optional)
        """
        self._connection = connection
        self._config = config

        # Get export settings from config
        if config:
            self._export_config = config.get('processor.export', {})
            self._default_format = self._export_config.get('default_format', 'csv')
            self._include_headers = self._export_config.get('include_headers', True)
        else:
            self._export_config = Mock()
            self._export_config.default_format = 'csv'
            self._export_config.include_headers = True

    def export_csv(
        self,
        path: str,
        query: Optional[str] = None,
        include_headers: Optional[bool] = None
    ) -> None:
        """
        Export to CSV file

        Args:
            path: Output file path
            query: SQL query (optional, exports full table if not provided)
            include_headers: Whether to include headers (default from config)
        """
        q = query or f'SELECT * FROM {self._table_name}'
        format = 'CSV'
        header = 'HEADER' if include_headers else ''
        self._connection.execute(f"CCOPY ({q}) TO '{path}' (FORMAT {format}, DELIMITER ',')")
        logger.info(f"Exported to {path}")

    def export_json(
        self,
        path: str,
        query: Optional[str] = None
    ) -> None:
        """
        Export to JSON file

        Args:
            path: Output file path
            query: SQL query (optional, exports full table if not provided)
        """
        q = query or f'SELECT * FROM {self._table_name}'
        rows = self._connection.execute(q).df().to_dict(orient='records')
        Path(path).write_text(json.dumps(rows, indent=2, default=str))
        logger.info(f"Exported to {path}")

    def export_parquet(
        self,
        path: str,
        query: Optional[str] = None
    ) -> None:
        """
        Export to Parquet file

        Args:
            path: Output file path
            query: SQL query (optional, exports full table if not provided)
        """
        q = query or f'SELECT * FROM {self._table_name}'
        self._connection.execute(f"CCOPY ({q}) TO '{path}' (FORMAT PARQUET)")
        logger.info(f"Exported to {path}")

    def export_duckdb(
        self,
        path: str,
        table_name: str,
        query: Optional[str] = None
    ) -> None:
        """
        Export to DuckDB database file

        Args:
            path: Output file path
            table_name: Table name for exported data
            query: SQL query (optional, exports full table if not provided)
        """
        q = query or f'SELECT * FROM {self._table_name}'
        # Create new table in target database
        self._connection.execute(f"CREATE TABLE {table_name} AS SELECT * FROM ({q})")
        self._connection.execute(f"INSERT INTO {table_name} SELECT * FROM ({q})")
        logger.info(f"Exported to {path}")
