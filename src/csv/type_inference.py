"""
Type inference for CSV columns with comprehensive type detection.

This module automatically infers data types from sample data, supporting
Integer, Float, String, Boolean, Date, and DateTime types with robust
null value handling and mixed-type detection.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd

logger = logging.getLogger(__name__)

# @MX:ANCHOR: [AUTO] Core schema inference function with comprehensive type detection
# @MX:REASON: Primary entry point for CSV type inference, called by upload API and schema endpoints
# @MX:SPEC: SPEC-CSV-001 AC-CSV-003, AC-CSV-013
def infer_schema(
    data_path: str,
    sample_rows: int = 1000,
    encoding: str = "utf-8"
) -> List[Dict[str, Any]]:
    """
    Infer schema (column names and types) from a CSV file.

    This function performs comprehensive type inference on CSV data by:
    1. Reading sample rows from the CSV file
    2. Analyzing each column for type patterns
    3. Detecting null values and mixed-type columns
    4. Returning detailed schema metadata

    Args:
        data_path: Path to the CSV file
        sample_rows: Number of rows to sample for inference (default: 1000)
        encoding: Character encoding of the file (default: "utf-8")

    Returns:
        List of column metadata dictionaries with keys:
        - name: Column name (str)
        - type: Inferred type (Integer, Float, String, Boolean, Date, DateTime)
        - nullable: Whether column contains null values (bool)
        - null_count: Number of null values in column (int)

    Raises:
        FileNotFoundError: If file does not exist
        ValueError: If file is empty or invalid

    Examples:
        >>> infer_schema('data.csv')
        [
            {'name': 'id', 'type': 'Integer', 'nullable': False, 'null_count': 0},
            {'name': 'price', 'type': 'Float', 'nullable': True, 'null_count': 5},
            {'name': 'active', 'type': 'Boolean', 'nullable': False, 'null_count': 0},
            {'name': 'created', 'type': 'DateTime', 'nullable': True, 'null_count': 2}
        ]
    """
    # Validate file path
    path = Path(data_path)
    if not path.exists():
        logger.error(f">>> [TYPE INFERENCE] File not found: {data_path}")
        raise FileNotFoundError(f"CSV file not found: {data_path}")

    if not path.is_file():
        logger.error(f">>> [TYPE INFERENCE] Path is not a file: {data_path}")
        raise ValueError(f"Path is not a file: {data_path}")

    if path.stat().st_size == 0:
        logger.warning(f">>> [TYPE INFERENCE] Empty file: {data_path}")
        raise ValueError(f"Empty file: {data_path}")

    # Read CSV sample with pandas for robust parsing
    try:
        df = pd.read_csv(
            data_path,
            encoding=encoding,
            nrows=sample_rows,
            dtype=str,  # Load all as string for type inference
            na_values=['', 'NULL', 'null', 'None', 'NA', 'N/A', 'NaN', 'nan'],
            keep_default_na=True,
            on_bad_lines='warn'  # Warn but don't fail on malformed rows
        )

        if df.empty:
            logger.warning(f">>> [TYPE INFERENCE] No data rows in file: {data_path}")
            return []

    except Exception as e:
        logger.error(
            f">>> [TYPE INFERENCE] Failed to read CSV file: {data_path}",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "file_path": data_path,
                "encoding": encoding
            }
        )
        raise ValueError(f"Failed to read CSV file: {e}") from e

    # Infer schema for each column
    schema = []

    for col_name in df.columns:
        column_data = df[col_name]

        # Analyze column
        col_info = _analyze_column(column_data, str(col_name))
        schema.append(col_info)

        logger.info(
            f">>> [TYPE INFERENCE] Column '{col_name}': "
            f"type={col_info['type']}, "
            f"nullable={col_info['nullable']}, "
            f"null_count={col_info['null_count']}"
        )

    logger.info(
        f">>> [TYPE INFERENCE] Inferred schema for {len(schema)} columns "
        f"from {data_path}"
    )

    return schema


def _analyze_column(series: pd.Series, col_name: str) -> Dict[str, Any]:
    """
    Analyze a pandas Series to infer type and null information.

    Args:
        series: pandas Series to analyze
        col_name: Name of the column

    Returns:
        Dictionary with type, nullable, and null_count information
    """
    # Count null values
    null_count = int(series.isna().sum())
    nullable = null_count > 0

    # Get non-null values for type inference
    non_null = series.dropna()

    if len(non_null) == 0:
        # All null values - default to String type
        return {
            'name': col_name,
            'type': 'String',
            'nullable': True,
            'null_count': null_count
        }

    # Convert all values to strings for type checking
    non_null_str = non_null.astype(str)

    # Infer type from sample
    inferred_type = _infer_type_from_values(non_null_str)

    return {
        'name': col_name,
        'type': inferred_type,
        'nullable': nullable,
        'null_count': null_count
    }


def _infer_type_from_values(values: pd.Series) -> str:
    """
    Infer data type from string values.

    Type inference follows this priority order:
    1. Integer - if all values parse as int
    2. Float - if all values parse as float
    3. Boolean - if all values are boolean representations
    4. DateTime - if all values are ISO 8601 datetime
    5. Date - if all values are ISO 8601 date
    6. String - default fallback

    Args:
        values: pandas Series with string values

    Returns:
        Inferred type name (Integer, Float, String, Boolean, Date, DateTime)
    """
    # Sample first 100 non-null values for performance
    sample = values.head(100) if len(values) > 100 else values

    # Try Integer
    if _is_integer_type(sample):
        return 'Integer'

    # Try Float
    if _is_float_type(sample):
        return 'Float'

    # Try Boolean
    if _is_boolean_type(sample):
        return 'Boolean'

    # Try DateTime
    if _is_datetime_type(sample):
        return 'DateTime'

    # Try Date
    if _is_date_type(sample):
        return 'Date'

    # Default to String
    return 'String'


def _is_integer_type(values: pd.Series) -> bool:
    """Check if all values are integers."""
    try:
        for val in values:
            # Check for decimal points (floats are not integers)
            if isinstance(val, str) and '.' in val:
                return False
            int(val)
        return True
    except (ValueError, TypeError):
        return False


def _is_float_type(values: pd.Series) -> bool:
    """Check if all values are floats."""
    try:
        for val in values:
            float(val)
        return True
    except (ValueError, TypeError):
        return False


def _is_boolean_type(values: pd.Series) -> bool:
    """Check if all values are boolean representations."""
    boolean_values = {
        'true', 'false', 'True', 'False', 'TRUE', 'FALSE',
        '1', '0', 'yes', 'no', 'Yes', 'No', 'YES', 'NO'
    }

    # Check if all values are in boolean set
    return all(val.lower() in boolean_values for val in values)


def _is_datetime_type(values: pd.Series) -> bool:
    """Check if all values are ISO 8601 datetime strings."""
    datetime_formats = [
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%dT%H:%M:%SZ',
        '%Y-%m-%dT%H:%M:%S.%f',
        '%Y-%m-%dT%H:%M:%S.%fZ',
    ]

    parsed_count = 0

    for val in values:
        parsed = False
        for fmt in datetime_formats:
            try:
                datetime.strptime(val, fmt)
                parsed = True
                break
            except ValueError:
                continue
        if not parsed:
            return False
        parsed_count += 1

    return parsed_count > 0


def _is_date_type(values: pd.Series) -> bool:
    """Check if all values are ISO 8601 date strings (YYYY-MM-DD)."""
    date_format = '%Y-%m-%d'

    for val in values:
        try:
            datetime.strptime(val, date_format)
        except ValueError:
            return False

    return True
