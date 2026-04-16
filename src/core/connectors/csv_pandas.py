"""
Pandas-based CSV Connector with robust NULL value handling.

This connector uses pandas for CSV parsing, which provides:
- Automatic NULL detection for empty strings
- Graceful type coercion with errors='coerce'
- Direct DuckDB integration via conn.register()

Key advantage over csv.DictReader:
Handles empty values ('') as NULLs automatically without manual detection.
"""

import os
import logging
from typing import Dict, List, Any, Iterator, Optional
from datetime import datetime
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class PandasCSVConnector:
    """
    CSV connector using pandas for robust NULL value handling.

    Key features:
    - Automatic NULL detection for empty strings, 'NA', 'null', etc.
    - Type-safe coercion with errors='coerce' (invalid → NaN)
    - Direct DuckDB integration via register()
    - Memory-efficient chunking for large files
    """

    # Standard NULL value representations
    MISSING_VALUES = ['', 'NA', 'N/A', 'null', 'NULL', 'None', 'none', 'NaN', 'nan', '-inf', 'inf']

    def __init__(self, delimiter: str = ',', has_header: bool = True, encoding: str = 'utf-8'):
        """
        Initialize Pandas CSV connector.

        Args:
            delimiter: Column separator (default: ',')
            has_header: Whether first row is header (default: True)
            encoding: File encoding (default: 'utf-8')
        """
        if not delimiter or len(delimiter) != 1:
            raise ValueError("Delimiter must be a single character")

        self.delimiter = delimiter
        self.has_header = has_header
        self.encoding = encoding

    # ========================================================================
    #  BaseConnector Interface Implementation
    # =========================================================================

    def connect(self, **kwargs) -> None:
        """Pandas connector doesn't require active connection."""
        pass

    def read(self, file_path: str, **kwargs) -> Iterator[Dict[str, Any]]:
        """
        Read CSV file and yield rows as dictionaries.

        Args:
            file_path: Path to CSV file
            **kwargs: Additional read options

        Yields:
            Dictionary representing a row with column names as keys
        """
        df = self.read_csv(file_path, **kwargs)
        for _, row in df.iterrows():
            # Replace NaN with None for JSON serialization
            yield {k: (None if pd.isna(v) else v) for k, v in row.items()}

    def validate(self, file_path: str) -> bool:
        """
        Validate CSV file.

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
        Get CSV file metadata.

        Args:
            file_path: Path to CSV file

        Returns:
            Dictionary with file statistics
        """
        return self.get_statistics(file_path)

    # ========================================================================
    #  Type Inference (NULL-Aware)
    # =========================================================================

    def _infer_type(self, series: pd.Series) -> str:
        """
        Infer DuckDB data type from pandas Series with NULL awareness.

        Args:
            series: pandas Series to analyze

        Returns:
            DuckDB type name (INTEGER, FLOAT, BOOLEAN, DATE, VARCHAR)
        """
        # Drop NaN values for type checking
        non_null = series.dropna()

        if len(non_null) == 0:
            return 'VARCHAR'  # All NULLs, default to VARCHAR

        # Sample first 100 non-null values for performance
        sample = non_null.head(100)

        # Try INTEGER
        try:
            # Check if all values are integers (no decimals)
            if pd.to_numeric(sample, errors='coerce').notna().all():
                # Check if values are actually integers (no .0 in string representation)
                if sample.apply(lambda x: str(x).isdigit() if isinstance(x, str) else float(x).is_integer() if isinstance(x, float) else True).all():
                    return 'INTEGER'
        except (ValueError, TypeError):
            pass

        # Try FLOAT
        try:
            if pd.to_numeric(sample, errors='coerce').notna().all():
                return 'FLOAT'
        except (ValueError, TypeError):
            pass

        # Try BOOLEAN
        boolean_values = {'true', 'false', 'TRUE', 'FALSE', 'True', 'False', '1', '0', 'yes', 'no'}
        if sample.astype(str).str.lower().isin(boolean_values).all():
            return 'BOOLEAN'

        # Try DATE
        try:
            pd.to_datetime(sample, errors='coerce')
            if pd.to_datetime(sample, errors='coerce').notna().all():
                return 'DATE'
        except (ValueError, TypeError):
            pass

        # Default to VARCHAR
        return 'VARCHAR'

    def infer_schema(self, file_path: str, max_rows: int = 1000) -> Dict[str, str]:
        """
        Infer schema from CSV file using pandas.

        Args:
            file_path: Path to CSV file
            max_rows: Maximum number of rows to sample for inference (default: 1000)

        Returns:
            Dictionary mapping column names to inferred DuckDB types
        """
        # Read sample of CSV
        df = pd.read_csv(
            file_path,
            delimiter=self.delimiter,
            header=0 if self.has_header else None,
            encoding=self.encoding,
            nrows=max_rows,
            na_values=self.MISSING_VALUES,
            keep_default_na=True,
            dtype=str,  # Load all as string for type inference
            on_bad_lines='skip',  # Skip malformed rows
        )

        # Infer type for each column
        schema = {}
        for col in df.columns:
            series = df[col]
            null_count = series.isna().sum()
            total_count = len(series)

            if null_count > 0:
                logger.info(
                    f">>> [PANDAS SCHEMA] Column '{col}' has {null_count}/{total_count} NULL values, "
                    f"inferring type from {total_count - null_count} non-null values"
                )

            schema[str(col)] = self._infer_type(series)

        logger.info(f">>> [PANDAS SCHEMA] Inferred schema for {len(schema)} columns from {file_path}")
        return schema

    # ========================================================================
    #  CSV Reading
    # =========================================================================

    def read_csv(self, file_path: str, **kwargs) -> pd.DataFrame:
        """
        Read CSV file into pandas DataFrame.

        Args:
            file_path: Path to CSV file
            **kwargs: Additional read options

        Returns:
            pandas DataFrame with NULL-aware parsing
        """
        self.validate_csv_path(file_path)

        df = pd.read_csv(
            file_path,
            delimiter=self.delimiter,
            header=0 if self.has_header else None,
            encoding=self.encoding,
            na_values=self.MISSING_VALUES,
            keep_default_na=True,
            dtype=str,  # Load all as string initially
            on_bad_lines='warn',  # Warn but don't fail on malformed rows
            **kwargs
        )

        # Strip whitespace from string columns
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].str.strip()

        return df

    # ========================================================================
    #  Statistics and Validation
    # =========================================================================

    def get_statistics(self, file_path: str) -> Dict[str, Any]:
        """
        Get statistics about CSV file.

        Args:
            file_path: Path to CSV file

        Returns:
            Dictionary with file statistics
        """
        self.validate_csv_path(file_path)

        df = self.read_csv(file_path, nrows=10000)  # Sample for performance

        return {
            'row_count': len(df),
            'column_count': len(df.columns),
            'columns': list(df.columns),
            'file_size': os.path.getsize(file_path),
            'file_size_mb': os.path.getsize(file_path) / (1024 * 1024),
            'null_counts': {col: int(df[col].isna().sum()) for col in df.columns},
            'memory_usage_mb': df.memory_usage(deep=True).sum() / (1024 * 1024)
        }

    def validate_csv_path(self, file_path: str) -> bool:
        """
        Validate CSV file path.

        Args:
            file_path: Path to CSV file

        Returns:
            True if valid

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is empty or invalid
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"CSV file not found: {file_path}")

        if os.path.getsize(file_path) == 0:
            raise ValueError(f"CSV file is empty: {file_path}")

        return True

    # ========================================================================
    #  DuckDB Integration
    # =========================================================================

    def register_with_duckdb(self, file_path: str, conn, table_name: str = 'csv_data') -> Dict[str, Any]:
        """
        Load CSV with pandas and register directly with DuckDB.

        This is the RECOMMENDED method for workflow execution as it:
        1. Handles NULL values automatically (empty strings → NaN)
        2. Bypasses CSV parsing issues in DuckDB
        3. Uses pandas' robust type coercion

        Args:
            file_path: Path to CSV file
            conn: DuckDB connection
            table_name: Name for registered table

        Returns:
            Dictionary with schema and metadata
        """
        # Load CSV with pandas (handles NULLs automatically)
        df = pd.read_csv(
            file_path,
            delimiter=self.delimiter,
            header=0 if self.has_header else None,
            encoding=self.encoding,
            na_values=self.MISSING_VALUES,
            keep_default_na=True,
            dtype=str,  # Load all as string for safety
            on_bad_lines='warn'
        )

        # Strip whitespace
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].str.strip()

        # Register with DuckDB (zero-copy if possible)
        conn.register(table_name, df)

        # Infer schema from DataFrame
        schema = {}
        for col in df.columns:
            series = df[col]
            null_count = series.isna().sum()

            if null_count > 0:
                logger.info(f">>> [PANDAS] Column '{col}' has {null_count} NULL values")

            schema[str(col)] = self._infer_type(series)

        logger.info(
            f">>> [PANDAS] Registered {len(df)} rows × {len(df.columns)} columns "
            f"as DuckDB table '{table_name}'"
        )

        return {
            'schema': schema,
            'table_name': table_name,
            'row_count': len(df),
            'column_count': len(df.columns),
            'encoding': self.encoding,
            'delimiter': self.delimiter
        }


# ========================================================================
#  Convenience Functions
# =========================================================================

def load_csv_with_pandas(file_path: str, conn, table_name: str = 'csv_data') -> Dict[str, Any]:
    """
    Convenience function to load CSV with pandas and register with DuckDB.

    Args:
        file_path: Path to CSV file
        conn: DuckDB connection
        table_name: Name for registered table

    Returns:
        Dictionary with schema and metadata
    """
    connector = PandasCSVConnector()
    return connector.register_with_duckdb(file_path, conn, table_name)


def infer_schema_with_pandas(file_path: str) -> Dict[str, str]:
    """
    Convenience function to infer schema using pandas.

    Args:
        file_path: Path to CSV file

    Returns:
        Dictionary mapping column names to DuckDB types
    """
    connector = PandasCSVConnector()
    return connector.infer_schema(file_path)
