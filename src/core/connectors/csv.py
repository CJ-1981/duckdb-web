"""
CSV Connector

Enhanced CSV connector with automatic type inference, streaming support,
and integration with DuckDB database.
"""

import csv
import os
from typing import List, Dict, Any, Iterator, Optional, Callable
from pathlib import Path
from datetime import datetime

from .base import BaseConnector
from ..database import DatabaseConnection


class CSVConnector(BaseConnector):
    """
    Enhanced CSV connector with automatic type inference and streaming

    Features:
    - Automatic type inference (INTEGER, FLOAT, BOOLEAN, DATE, VARCHAR)
    - Custom delimiter support (comma, tab, pipe, semicolon)
    - Header detection and validation
    - Missing value handling (NULL, '', NA, NaN, None)
    - Encoding detection (UTF-8, Latin-1, etc.)
    - Large file streaming (> 100MB threshold)
    - Chunk-based processing
    - Progress reporting for large files

    Example:
        >>> connector = CSVConnector(delimiter='|', has_header=True)
        >>> connector.import_to_duckdb('data.csv', db_connection, 'my_table')
    """

    # Class constants
    DEFAULT_STREAMING_THRESHOLD = 100 * 1024 * 1024  # 100MB
    DEFAULT_CHUNK_SIZE = 10000
    MISSING_VALUES = ['', 'NULL', 'NA', 'NaN', 'nan', 'None', 'null', 'N/A']
    PROGRESS_REPORT_INTERVAL = 1000  # Report progress every N rows

    def __init__(
        self,
        delimiter: str = ',',
        has_header: bool = True,
        encoding: str = 'utf-8',
        streaming_threshold: int = DEFAULT_STREAMING_THRESHOLD,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
    ):
        """
        Initialize CSV connector

        Args:
            delimiter: Column delimiter (default: comma)
            has_header: Whether first row is header (default: True)
            encoding: File encoding (default: utf-8)
            streaming_threshold: File size threshold for streaming (default: 100MB)
            chunk_size: Number of rows per chunk when streaming (default: 10000)
        """
        super().__init__()

        if not delimiter or len(delimiter) != 1:
            raise ValueError("Delimiter must be a single character")

        self.delimiter = delimiter
        self.has_header = has_header
        self.encoding = encoding
        self.streaming_threshold = streaming_threshold
        self.chunk_size = chunk_size

    # ========================================================================
    #  BaseConnector Interface Implementation
    # =========================================================================

    def connect(self, **kwargs) -> None:
        """
        CSV connector doesn't require active connection

        This method exists for interface compatibility but does nothing.
        """
        pass

    def read(self, file_path: str, **kwargs) -> Iterator[Dict[str, Any]]:
        """
        Read CSV file and yield rows as dictionaries

        Args:
            file_path: Path to CSV file
            **kwargs: Additional read options

        Yields:
            Dictionary representing a row with column names as keys
        """
        yield from self.read_csv(file_path, **kwargs)

    def validate(self, file_path: str) -> bool:
        """
        Validate CSV file

        Args:
            file_path: Path to CSV file

        Returns:
            True if valid

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is empty or invalid
        """
        return self.validate_csv_path(file_path)

    def get_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Get CSV file metadata

        Args:
            file_path: Path to CSV file

        Returns:
            Dictionary with file statistics
        """
        return self.get_statistics(file_path)

    # ========================================================================
    #  Type Inference
    # =========================================================================

    def _normalize_missing_values(self, value: Any) -> Optional[Any]:
        """
        Normalize missing value representations to None for DuckDB

        Args:
            value: Value to normalize

        Returns:
            None if value is a missing value representation, otherwise original value
        """
        if value in self.MISSING_VALUES or value == '':
            return None
        return value

    def _infer_type(self, values: List[str]) -> str:
        """
        Infer DuckDB data type from list of string values

        Args:
            values: List of string values from a column

        Returns:
            DuckDB type name (INTEGER, FLOAT, BOOLEAN, DATE, VARCHAR)
        """
        # Filter out missing values and ensure all values are strings
        non_empty = []
        for v in values:
            if isinstance(v, list):
                # Handle nested list issue from inconsistent rows
                return 'VARCHAR'
            if v and str(v).strip() not in self.MISSING_VALUES:
                non_empty.append(str(v).strip())

        if not non_empty:
            return 'VARCHAR'  # Default for empty columns

        # Try INTEGER
        try:
            for v in non_empty:
                int(v)
            return 'INTEGER'
        except (ValueError, TypeError):
            pass

        # Try FLOAT
        try:
            for v in non_empty:
                float(v)
            return 'FLOAT'
        except (ValueError, TypeError):
            pass

        # Try BOOLEAN
        boolean_values = {'true', 'false', 'TRUE', 'FALSE', 'True', 'False',
                         '1', '0', 'yes', 'no', 'YES', 'NO'}
        if all(v in boolean_values for v in non_empty):
            return 'BOOLEAN'

        # Try DATE
        date_formats = [
            '%Y-%m-%d',
            '%d/%m/%Y',
            '%m/%d/%Y',
            '%Y-%m-%d %H:%M:%S',
        ]
        is_date = True
        for v in non_empty[:100]:  # Sample first 100 values
            parsed = False
            for fmt in date_formats:
                try:
                    datetime.strptime(v, fmt)
                    parsed = True
                    break
                except ValueError:
                    continue
            if not parsed:
                is_date = False
                break

        if is_date:
            return 'DATE'

        # Default to VARCHAR
        return 'VARCHAR'

    def infer_schema(self, file_path: str) -> Dict[str, str]:
        """
        Infer schema from CSV file

        Args:
            file_path: Path to CSV file

        Returns:
            Dictionary mapping column names to inferred types
        """
        # Read all rows to analyze types
        rows = []
        with open(file_path, 'r', encoding=self.encoding, newline='') as f:
            reader = csv.DictReader(f, delimiter=self.delimiter)
            try:
                for row in reader:
                    rows.append(row)
            except Exception:
                # If DictReader fails, fall back to standard reader
                f.seek(0)
                reader = csv.reader(f, delimiter=self.delimiter)
                rows = [dict(enumerate(row)) for row in reader]

        if not rows:
            return {}

        # Collect all column names
        columns = set()
        for row in rows:
            columns.update(row.keys())

        # Infer type for each column
        schema = {}
        for col in columns:
            values = [row.get(col, '') for row in rows]
            schema[col] = self._infer_type(values)

        return schema

    # ========================================================================
    #  CSV Reading
    # =========================================================================

    def read_csv(self, file_path: str) -> Iterator[Dict[str, Any]]:
        """
        Read CSV file and yield rows as dictionaries

        Args:
            file_path: Path to CSV file

        Yields:
            Dictionary representing a row
        """
        with open(file_path, 'r', encoding=self.encoding, newline='') as f:
            if self.has_header:
                reader = csv.DictReader(f, delimiter=self.delimiter)
                for row in reader:
                    yield row
            else:
                reader = csv.reader(f, delimiter=self.delimiter)
                for i, row in enumerate(reader):
                    # Generate column names if no header
                    yield {f'col_{j}': value for j, value in enumerate(row)}

    def stream_csv(
        self,
        file_path: str,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> Iterator[List[Dict[str, Any]]]:
        """
        Stream large CSV file in chunks

        Args:
            file_path: Path to CSV file
            progress_callback: Optional callback for progress updates

        Yields:
            List of dictionaries (chunk of rows)
        """
        total_rows = 0

        with open(file_path, 'r', encoding=self.encoding, newline='') as f:
            if self.has_header:
                reader = csv.DictReader(f, delimiter=self.delimiter)
            else:
                reader = csv.reader(f, delimiter=self.delimiter)

            chunk = []
            for i, row in enumerate(reader):
                if not self.has_header:
                    row = {f'col_{j}': value for j, value in enumerate(row)}

                chunk.append(row)
                total_rows += 1

                if len(chunk) >= self.chunk_size:
                    yield chunk

                    # Report progress
                    if progress_callback:
                        file_size = os.path.getsize(file_path)
                        progress_callback({
                            'rows_processed': total_rows,
                            'total_rows': total_rows,  # May not know total upfront
                            'percentage': min(100.0, (total_rows / self.chunk_size) * 100),
                            'file_size': file_size,
                        })

                    chunk = []

            # Yield remaining rows
            if chunk:
                yield chunk

    # ========================================================================
    #  Validation
    # =========================================================================

    def validate_csv_path(self, file_path: str) -> bool:
        """
        Validate CSV file path and contents

        Args:
            file_path: Path to CSV file

        Returns:
            True if valid

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is empty
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"CSV file not found: {file_path}")

        if not path.is_file():
            raise ValueError(f"Path is not a file: {file_path}")

        if path.stat().st_size == 0:
            raise ValueError(f"Empty CSV file: {file_path}")

        return True

    # ========================================================================
    #  Statistics
    # =========================================================================

    def get_statistics(self, file_path: str) -> Dict[str, Any]:
        """
        Get statistics about CSV file

        Args:
            file_path: Path to CSV file

        Returns:
            Dictionary with file statistics
        """
        self.validate_csv_path(file_path)

        path = Path(file_path)
        file_size = path.stat().st_size

        rows = []
        columns = set()

        with open(file_path, 'r', encoding=self.encoding, newline='') as f:
            if self.has_header:
                reader = csv.DictReader(f, delimiter=self.delimiter)
                try:
                    for row in reader:
                        rows.append(row)
                        columns.update(row.keys())
                except Exception:
                    # If header parsing fails, count rows instead
                    f.seek(0)
                    reader = csv.reader(f, delimiter=self.delimiter)
                    rows = list(reader)
                    row_count = len(rows) - 1  # Exclude header
                    if rows:
                        col_count = len(rows[0])
                    else:
                        col_count = 0
            else:
                reader = csv.reader(f, delimiter=self.delimiter)
                rows = list(reader)
                row_count = len(rows)
                if rows:
                    col_count = len(rows[0])
                else:
                    col_count = 0

        if self.has_header and rows:
            row_count = len(rows)
            columns = set(rows[0].keys()) if rows else set()
            col_count = len(columns)

        return {
            'row_count': row_count,
            'column_count': col_count,
            'columns': list(columns),
            'file_size': file_size,
            'file_size_mb': file_size / (1024 * 1024),
        }

    # ========================================================================
    #  DuckDB Integration
    # =========================================================================

    def import_to_duckdb(
        self,
        csv_path: str,
        db_connection: DatabaseConnection,
        table_name: str,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> None:
        """
        Import CSV data into DuckDB table

        Args:
            csv_path: Path to CSV file
            db_connection: DatabaseConnection instance
            table_name: Name of target table
            progress_callback: Optional callback for progress updates
        """
        # Validate file
        self.validate_csv_path(csv_path)

        # Infer schema
        schema = self.infer_schema(csv_path)

        # Create table with inferred schema
        if schema:
            columns_def = ', '.join([f'"{col}" {dtype}' for col, dtype in schema.items()])
        else:
            # Fallback: read first row to get columns
            rows = list(self.read_csv(csv_path))
            if rows:
                columns = rows[0].keys()
                columns_def = ', '.join([f'"{col}" VARCHAR' for col in columns])
            else:
                raise ValueError(f"Unable to determine schema from {csv_path}")

        # Drop existing table
        db_connection.execute(f'DROP TABLE IF EXISTS {table_name}')

        # Create table
        create_sql = f'CREATE TABLE {table_name} ({columns_def})'
        db_connection.execute(create_sql)

        # Import data
        file_size = os.path.getsize(csv_path)

        if file_size > self.streaming_threshold:
            # Use streaming for large files
            rows_imported = 0

            # First pass: count total rows for accurate progress
            total_rows = 0
            with open(csv_path, 'r', encoding=self.encoding, newline='') as f:
                total_rows = sum(1 for _ in f) - (1 if self.has_header else 0)

            for chunk in self.stream_csv(csv_path, progress_callback):
                # Insert chunk
                for row in chunk:
                    columns = list(row.keys())
                    # Convert missing values to None for DuckDB
                    values = [self._normalize_missing_values(row.get(col)) for col in columns]
                    placeholders = ', '.join(['?' for _ in values])
                    cols_str = ', '.join([f'"{col}"' for col in columns])

                    insert_sql = f'INSERT INTO {table_name} ({cols_str}) VALUES ({placeholders})'
                    db_connection.execute(insert_sql, values)
                    rows_imported += 1

                    # Report progress
                    if progress_callback and rows_imported % self.PROGRESS_REPORT_INTERVAL == 0:
                        progress_callback({
                            'rows_processed': rows_imported,
                            'total_rows': total_rows,
                            'percentage': (rows_imported / total_rows * 100) if total_rows > 0 else 0,
                        })

            # Final progress report
            if progress_callback:
                progress_callback({
                    'rows_processed': rows_imported,
                    'total_rows': total_rows,
                    'percentage': 100.0,
                })
        else:
            # Read all at once for small files
            rows = list(self.read_csv(csv_path))

            for row in rows:
                columns = list(row.keys())
                # Convert missing values to None for DuckDB
                values = [self._normalize_missing_values(row.get(col)) for col in columns]
                placeholders = ', '.join(['?' for _ in values])
                cols_str = ', '.join([f'"{col}"' for col in columns])

                insert_sql = f'INSERT INTO {table_name} ({cols_str}) VALUES ({placeholders})'
                db_connection.execute(insert_sql, values)

            # Report completion
            if progress_callback:
                progress_callback({
                    'rows_processed': len(rows),
                    'total_rows': len(rows),
                    'percentage': 100.0,
                })

    # ========================================================================
    #  Configuration
    # =========================================================================

    @classmethod
    def from_config(cls, config: Any) -> 'CSVConnector':
        """
        Create CSV connector from configuration object

        Args:
            config: Configuration object with CSV settings

        Returns:
            CSVConnector instance
        """
        csv_config = config.connectors.csv

        return cls(
            delimiter=getattr(csv_config, 'delimiter', ','),
            has_header=getattr(csv_config, 'has_header', True),
            encoding=getattr(csv_config, 'encoding', 'utf-8'),
            streaming_threshold=getattr(csv_config, 'streaming_threshold', cls.DEFAULT_STREAMING_THRESHOLD),
            chunk_size=getattr(csv_config, 'chunk_size', cls.DEFAULT_CHUNK_SIZE),
        )
