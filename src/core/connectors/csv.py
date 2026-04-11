"""
CSV Connector

Enhanced CSV connector with automatic type inference, streaming support,
and integration with DuckDB database.
"""

import csv
import os
import logging
from typing import List, Dict, Any, Iterator, Optional, Callable
from pathlib import Path
from datetime import datetime

from .base import BaseConnector
from ..database import DatabaseConnection

logger = logging.getLogger(__name__)


def clean_invisible_unicode(text: str) -> str:
    """
    Remove invisible Unicode characters that can cause SQL errors or display issues.

    This utility function strips BOM (Byte Order Mark), zero-width characters,
    and converts non-breaking spaces to regular spaces. Used by both CSV
    column name cleaning and SQL identifier quoting.

    Args:
        text: Raw string potentially containing invisible Unicode characters

    Returns:
        Cleaned string with invisible characters removed

    Examples:
        >>> clean_invisible_unicode('﻿Hello')  # BOM prefix
        'Hello'
        >>> clean_invisible_unicode('Hello\\u200bWorld')  # Zero Width Space
        'HelloWorld'
        >>> clean_invisible_unicode('Hello\\u00a0World')  # Non-breaking space
        'Hello World'
    """
    if not text:
        return text

    # Ensure we are working with a string
    cleaned = str(text) if not isinstance(text, str) else text
    
    cleaned = cleaned.replace('\ufeff', '')  # BOM (Byte Order Mark)
    cleaned = cleaned.replace('\u200b', '')  # Zero Width Space
    cleaned = cleaned.replace('\u200c', '')  # Zero Width Non-Joiner
    cleaned = cleaned.replace('\u200d', '')  # Zero Width Joiner
    cleaned = cleaned.replace('\u00a0', ' ')  # Non-breaking space to regular space
    cleaned = cleaned.strip()

    return cleaned


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

    def _clean_korean_number(self, value: str) -> str:
        """
        Clean Korean number format for type inference

        Handles Korean number formats including:
        - Commas as thousand separators (1,000,000)
        - Currency symbols (₩, $, ¥, €, £)
        - Negative numbers in parentheses ((1,000) → -1000)
        - Leading/trailing whitespace

        Args:
            value: Raw string value from CSV

        Returns:
            Cleaned string ready for type conversion
        """
        if not value:
            return '0'

        cleaned = value.strip()

        # Remove currency symbols
        cleaned = cleaned.replace('₩', '')  # Won
        cleaned = cleaned.replace('$', '')  # Dollar
        cleaned = cleaned.replace('¥', '')  # Yen
        cleaned = cleaned.replace('€', '')  # Euro
        cleaned = cleaned.replace('£', '')  # Pound

        # Remove commas (thousand separators)
        cleaned = cleaned.replace(',', '')

        # Handle negative numbers in parentheses: (1,000) → -1000
        if cleaned.startswith('(') and cleaned.endswith(')'):
            cleaned = '-' + cleaned[1:-1]

        # Handle edge case: just a minus sign or empty after cleaning
        if not cleaned or cleaned == '-':
            return '0'

        return cleaned

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

        # Try INTEGER with Korean format cleaning
        try:
            for v in non_empty:
                cleaned = self._clean_korean_number(v)
                int(cleaned)
            return 'INTEGER'
        except (ValueError, TypeError):
            pass

        # Try FLOAT with Korean format cleaning
        try:
            for v in non_empty:
                cleaned = self._clean_korean_number(v)
                float(cleaned)
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

    def infer_schema(self, file_path: str, max_rows: int = 1000) -> Dict[str, str]:
        """
        Infer schema from CSV file

        Args:
            file_path: Path to CSV file
            max_rows: Maximum number of rows to sample for inference (default: 1000)

        Returns:
            Dictionary mapping column names to inferred types
        """
        # Read limited rows to analyze types
        rows = []
        encodings_to_try = [self.encoding, 'utf-8-sig', 'cp949', 'euc-kr', 'utf-16', 'latin-1']
        # Remove duplicates while preserving order
        encodings_to_try = list(dict.fromkeys([e for e in encodings_to_try if e]))

        last_error = None
        success = False
        fallback_enc = 'utf-8'  # Initialize with default

        for encoding in encodings_to_try:
            try:
                # First, sniff delimiter with this encoding
                with open(file_path, 'r', encoding=encoding, newline='') as f:
                    sample = f.read(8192)
                    if not sample:
                        continue
                    try:
                        dialect = csv.Sniffer().sniff(sample, delimiters=',\t;|')
                        self.delimiter = dialect.delimiter
                    except Exception:
                        pass # Keep current delimiter

                # Now read rows
                with open(file_path, 'r', encoding=encoding, newline='') as f:
                    reader = csv.DictReader(f, delimiter=self.delimiter)
                    for i, row in enumerate(reader):
                        if i >= max_rows:
                            break
                        # Filter out null characters and trim keys/values
                        clean_row = {
                            str(k).strip(): (str(v).strip() if v is not None else None) 
                            for k, v in row.items() if k is not None
                        }
                        rows.append(clean_row)
                
                if rows:
                    success = True
                    self.encoding = encoding
                    fallback_enc = encoding  # Track for fallback use
                    break
            except (UnicodeDecodeError, Exception) as e:
                last_error = e
                rows = []
                continue
                
        if not success:
            # Log detailed error information for CSV parsing failures
            logger.error(
                f">>> [CSV PARSE] Failed to parse CSV file with DictReader: {file_path}",
                extra={
                    "error": str(last_error),
                    "error_type": type(last_error).__name__ if last_error else "Unknown",
                    "file_path": file_path,
                    "encodings_tried": encodings_to_try,
                    "delimiter": self.delimiter,
                    "has_header": self.has_header
                }
            )
            
            # Use DuckDB as a fallback for schema inference if DictReader failed
            # This is much more robust for messy files
            try:
                import duckdb
                conn = duckdb.connect(database=':memory:')
                # Try reading with auto-detection
                # Treat empty strings as NULL during CSV load
                # Note: read_csv_auto automatically detects encoding
                rel = conn.execute("SELECT * FROM read_csv_auto(?, ALL_VARCHAR=TRUE, nullstr='') LIMIT 100", [file_path])
                # Convert to list of dictionaries directly, avoiding .df() conversion issues
                columns = [desc[0] for desc in rel.description]
                rows = [dict(zip(columns, row)) for row in rel.fetchall()]
                if rows:
                    success = True
                    # Set default encoding since DuckDB auto-detects
                    self.encoding = 'utf-8'
                    logger.info(f">>> [CSV FALLBACK] Successfully inferred schema using DuckDB for {file_path} (encoding: auto-detected)")
            except Exception as de:
                logger.error(f">>> [CSV FALLBACK] DuckDB inference also failed: {de}")

        if not rows:
            return {}

        # Collect all column names, stripping any weird characters
        columns = set()
        for row in rows:
            columns.update(row.keys())
        
        # Clean column names (strip BOM, nulls, etc.)
        cleaned_columns = {col: clean_invisible_unicode(str(col)) for col in columns}

        # Infer type for each column
        schema = {}
        for raw_col, clean_col in cleaned_columns.items():
            values = [row.get(raw_col, '') for row in rows]
            schema[clean_col] = self._infer_type(values)

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
            logger.error(
                f">>> [CSV VALIDATION] CSV file not found: {file_path}",
                extra={
                    "file_path": file_path,
                    "resolved_path": str(path.absolute()),
                    "error": "FileNotFoundError"
                }
            )
            raise FileNotFoundError(f"CSV file not found: {file_path}")

        if not path.is_file():
            logger.error(
                f">>> [CSV VALIDATION] Path is not a file: {file_path}",
                extra={
                    "file_path": file_path,
                    "resolved_path": str(path.absolute()),
                    "error": "NotAFileError"
                }
            )
            raise ValueError(f"Path is not a file: {file_path}")

        if path.stat().st_size == 0:
            logger.warning(
                f">>> [CSV VALIDATION] Empty CSV file: {file_path}",
                extra={
                    "file_path": file_path,
                    "file_size": 0,
                    "error": "EmptyFileError"
                }
            )
            raise ValueError(f"Empty CSV file: {file_path}")

        logger.debug(f">>> [CSV VALIDATION] File validated successfully: {file_path}")
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
        row_count = 0
        col_count = 0

        with open(file_path, 'r', encoding=self.encoding, newline='') as f:
            if self.has_header:
                reader = csv.DictReader(f, delimiter=self.delimiter)
                try:
                    for row in reader:
                        rows.append(row)
                        columns.update(row.keys())
                except Exception as e:
                    # Log detailed error for header parsing failures
                    logger.error(
                        f">>> [CSV STATISTICS] Failed to parse CSV header in: {file_path}",
                        extra={
                            "error": str(e),
                            "error_type": type(e).__name__,
                            "file_path": file_path,
                            "encoding": self.encoding,
                            "delimiter": self.delimiter
                        }
                    )
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
                    # csv.reader returns lists, not dicts
                    col_count = len(rows[0])
                else:
                    col_count = 0

        if self.has_header and rows:
            row_count = len(rows)
            # Handle both DictReader (dicts) and reader (lists)
            if isinstance(rows[0], dict):
                columns = set(rows[0].keys())
            else:
                # For csv.reader, rows are lists, use integer indices
                columns = set(range(len(rows[0]))) if rows and rows[0] else set()
            col_count = len(columns)

        return {
            'row_count': row_count,
            'column_count': col_count,
            # Convert all column names to strings (handles fallback from integer keys)
            'columns': [str(col) for col in list(columns)],
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
            # Ensure all column names are strings (handles fallback from integer keys)
            columns_def = ', '.join([f'"{str(col)}" {dtype}' for col, dtype in schema.items()])
        else:
            # Fallback: read first row to get columns
            rows = list(self.read_csv(csv_path))
            if rows:
                columns = rows[0].keys()
                # Ensure all column names are strings (handles fallback from integer keys)
                columns_def = ', '.join([f'"{str(col)}" VARCHAR' for col in columns])
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
                    # Ensure all column names are strings (handles fallback from integer keys)
                    cols_str = ', '.join([f'"{str(col)}"' for col in columns])

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
                # Ensure all column names are strings (handles fallback from integer keys)
                cols_str = ', '.join([f'"{str(col)}"' for col in columns])

                insert_sql = f'INSERT INTO {table_name} ({cols_str}) VALUES ({placeholders})'
                db_connection.execute(insert_sql, values)

            # Report completion
            if progress_callback:
                progress_callback({
                    'rows_processed': len(rows),
                    'total_rows': len(rows),
                    'percentage': 100.0,
                })

    def _clean_column_name(self, name: Any) -> str:
        """
        Clean column name by removing invisible Unicode characters.

        Args:
            name: Raw column name from CSV (string or integer index)

        Returns:
            Cleaned column name with BOM and invisible characters removed
        """
        # Convert to string if it's an integer (from fallback parsing)
        str_name = str(name) if not isinstance(name, str) else name
        return clean_invisible_unicode(str_name)

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
