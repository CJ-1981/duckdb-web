"""
Unit tests for type inference module.

This test suite validates the type inference system for CSV columns, covering:
- Integer, Float, Boolean, Date, DateTime type detection
- Null value handling
- Mixed-type column handling
- Edge cases and boundary conditions
"""

import os
import tempfile
from pathlib import Path
from typing import List, Dict, Any
import pytest

from src.csv.type_inference import infer_schema
from src.csv.encoding_detector import detect_encoding


# ========================================================================
#  Test Fixtures
# ========================================================================

@pytest.fixture
def sample_csv_dir() -> Path:
    """Path to directory containing test CSV fixtures."""
    return Path(__file__).parent / "fixtures" / "test_data" / "type_inference_samples"


@pytest.fixture
def create_temp_csv():
    """Factory fixture to create temporary CSV files for testing."""
    def _create_csv(filename: str, content: str) -> str:
        """Create a temporary CSV file with given content.

        Args:
            filename: Name for the temporary file
            content: CSV content as string

        Returns:
            Absolute path to created file
        """
        temp_dir = tempfile.mkdtemp()
        file_path = os.path.join(temp_dir, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return file_path
    return _create_csv


# ========================================================================
#  Characterization Tests - Preserve Existing Behavior
# ========================================================================

def test_characterize_existing_csv_connector_type_inference():
    """Characterize existing type inference behavior from csv.py.

    This test documents the current behavior of CSVConnector._infer_type()
    to ensure the new module preserves expected patterns.
    """
    # Import existing connector
    from src.core.connectors.csv import CSVConnector

    connector = CSVConnector()

    # Test Integer inference
    int_values = ["1", "42", "-10", "1000"]
    assert connector._infer_type(int_values) == 'INTEGER'

    # Test Float inference
    float_values = ["1.5", "3.14", "-0.01", "0.0"]
    assert connector._infer_type(float_values) == 'FLOAT'

    # Test Boolean inference
    bool_values = ["true", "false", "1", "0"]
    assert connector._infer_type(bool_values) == 'BOOLEAN'

    # Test VARCHAR default
    mixed_values = ["1", "hello", "3.14"]
    assert connector._infer_type(mixed_values) == 'VARCHAR'


def test_characterize_existing_pandas_type_inference():
    """Characterize existing pandas type inference behavior.

    This test documents the current behavior of PandasCSVConnector._infer_type()
    to ensure the new module aligns with pandas-based patterns.

    NOTE: Pandas _infer_type returns 'FLOAT' for integers because pd.to_numeric
    converts everything to float64 by default. This is expected behavior.
    """
    # Import existing pandas connector
    from src.core.connectors.csv_pandas import PandasCSVConnector
    import pandas as pd

    connector = PandasCSVConnector()

    # Test with pandas Series - integers become FLOAT in pandas
    int_series = pd.Series(["1", "42", "-10", "1000"])
    assert connector._infer_type(int_series) == 'FLOAT'  # pandas converts to float64

    # Test with actual floats
    float_series = pd.Series(["1.5", "3.14", "-0.01", "0.0"])
    assert connector._infer_type(float_series) == 'FLOAT'

    # Boolean detection still works
    bool_series = pd.Series(["true", "false", "1", "0"])
    assert connector._infer_type(bool_series) == 'BOOLEAN'


# ========================================================================
#  Specification Tests - Type Inference
# ========================================================================

def test_type_inference_integer(sample_csv_dir):
    """Test Integer type inference (AC-CSV-003).

    Given: A CSV file with pure integer column
    When: Schema inference is performed
    Then: Column type should be 'Integer'
    """
    csv_path = sample_csv_dir / "integer_sample.csv"

    if not csv_path.exists():
        pytest.skip(f"Test fixture not found: {csv_path}")

    encoding, _ = detect_encoding(str(csv_path))
    schema = infer_schema(str(csv_path), sample_rows=100, encoding=encoding)

    assert len(schema) > 0, "Schema should have at least one column"

    # Find integer column
    int_col = next((col for col in schema if col['name'] == 'id'), None)
    assert int_col is not None, "Should find 'id' column"
    assert int_col['type'] == 'Integer', f"Expected Integer, got {int_col['type']}"


def test_type_inference_float(sample_csv_dir):
    """Test Float type inference (AC-CSV-003).

    Given: A CSV file with pure float column
    When: Schema inference is performed
    Then: Column type should be 'Float'
    """
    csv_path = sample_csv_dir / "float_sample.csv"

    if not csv_path.exists():
        pytest.skip(f"Test fixture not found: {csv_path}")

    encoding, _ = detect_encoding(str(csv_path))
    schema = infer_schema(str(csv_path), sample_rows=100, encoding=encoding)

    float_col = next((col for col in schema if col['name'] == 'price'), None)
    assert float_col is not None, "Should find 'price' column"
    assert float_col['type'] == 'Float', f"Expected Float, got {float_col['type']}"


def test_type_inference_boolean(sample_csv_dir):
    """Test Boolean type inference (AC-CSV-003).

    Given: A CSV file with boolean values
    When: Schema inference is performed
    Then: Column type should be 'Boolean'
    """
    csv_path = sample_csv_dir / "boolean_sample.csv"

    if not csv_path.exists():
        pytest.skip(f"Test fixture not found: {csv_path}")

    encoding, _ = detect_encoding(str(csv_path))
    schema = infer_schema(str(csv_path), sample_rows=100, encoding=encoding)

    bool_col = next((col for col in schema if col['name'] == 'active'), None)
    assert bool_col is not None, "Should find 'active' column"
    assert bool_col['type'] == 'Boolean', f"Expected Boolean, got {bool_col['type']}"


def test_type_inference_date(sample_csv_dir):
    """Test Date type inference (AC-CSV-003).

    Given: A CSV file with date values (YYYY-MM-DD)
    When: Schema inference is performed
    Then: Column type should be 'Date'
    """
    csv_path = sample_csv_dir / "date_sample.csv"

    if not csv_path.exists():
        pytest.skip(f"Test fixture not found: {csv_path}")

    encoding, _ = detect_encoding(str(csv_path))
    schema = infer_schema(str(csv_path), sample_rows=100, encoding=encoding)

    date_col = next((col for col in schema if col['name'] == 'birth_date'), None)
    assert date_col is not None, "Should find 'birth_date' column"
    assert date_col['type'] == 'Date', f"Expected Date, got {date_col['type']}"


def test_type_inference_datetime(sample_csv_dir):
    """Test DateTime type inference (AC-CSV-003).

    Given: A CSV file with datetime values (ISO 8601)
    When: Schema inference is performed
    Then: Column type should be 'DateTime'
    """
    csv_path = sample_csv_dir / "datetime_sample.csv"

    if not csv_path.exists():
        pytest.skip(f"Test fixture not found: {csv_path}")

    encoding, _ = detect_encoding(str(csv_path))
    schema = infer_schema(str(csv_path), sample_rows=100, encoding=encoding)

    datetime_col = next((col for col in schema if col['name'] == 'created_at'), None)
    assert datetime_col is not None, "Should find 'created_at' column"
    assert datetime_col['type'] == 'DateTime', f"Expected DateTime, got {datetime_col['type']}"


def test_type_inference_string_default(sample_csv_dir):
    """Test String type default for unrecognizable types (AC-CSV-003).

    Given: A CSV file with text values
    When: Schema inference is performed
    Then: Column type should be 'String'
    """
    csv_path = sample_csv_dir / "string_sample.csv"

    if not csv_path.exists():
        pytest.skip(f"Test fixture not found: {csv_path}")

    encoding, _ = detect_encoding(str(csv_path))
    schema = infer_schema(str(csv_path), sample_rows=100, encoding=encoding)

    str_col = next((col for col in schema if col['name'] == 'name'), None)
    assert str_col is not None, "Should find 'name' column"
    assert str_col['type'] == 'String', f"Expected String, got {str_col['type']}"


# ========================================================================
#  Null Value Handling Tests
# ========================================================================

def test_null_value_handling(sample_csv_dir):
    """Test null value handling (AC-CSV-013).

    Given: A CSV file with various null representations
    When: Schema inference is performed
    Then: Null values should be counted correctly without type conversion
    """
    csv_path = sample_csv_dir / "null_sample.csv"

    if not csv_path.exists():
        pytest.skip(f"Test fixture not found: {csv_path}")

    encoding, _ = detect_encoding(str(csv_path))
    schema = infer_schema(str(csv_path), sample_rows=100, encoding=encoding)

    # Check that nullable flag is set correctly
    for col in schema:
        if col['null_count'] > 0:
            assert col['nullable'] is True, f"Column {col['name']} should be nullable"


# ========================================================================
#  Mixed-Type Column Tests
# ========================================================================

def test_mixed_type_column_defaults_to_string(sample_csv_dir):
    """Test mixed-type columns default to String (AC-CSV-013).

    Given: A CSV file with mixed types in same column
    When: Schema inference is performed
    Then: Column type should be 'String'
    """
    csv_path = sample_csv_dir / "mixed_type_sample.csv"

    if not csv_path.exists():
        pytest.skip(f"Test fixture not found: {csv_path}")

    encoding, _ = detect_encoding(str(csv_path))
    schema = infer_schema(str(csv_path), sample_rows=100, encoding=encoding)

    mixed_col = next((col for col in schema if col['name'] == 'mixed_data'), None)
    assert mixed_col is not None, "Should find 'mixed_data' column"
    assert mixed_col['type'] == 'String', f"Expected String for mixed types, got {mixed_col['type']}"


# ========================================================================
#  Edge Cases and Error Handling
# ========================================================================

def test_empty_file_error(create_temp_csv):
    """Test error handling for empty files.

    Given: An empty CSV file
    When: Schema inference is performed
    Then: Should raise ValueError
    """
    csv_path = create_temp_csv("empty.csv", "")

    with pytest.raises(ValueError, match="Empty file"):
        infer_schema(csv_path)


def test_file_not_found_error():
    """Test error handling for missing files.

    Given: A non-existent file path
    When: Schema inference is performed
    Then: Should raise FileNotFoundError
    """
    with pytest.raises(FileNotFoundError, match="CSV file not found"):
        infer_schema("/nonexistent/path/to/file.csv")


def test_single_column_detection(create_temp_csv):
    """Test schema inference for single-column CSV.

    Given: A CSV file with only one column
    When: Schema inference is performed
    Then: Should return schema with one column
    """
    content = "name\nAlice\nBob\nCharlie"
    csv_path = create_temp_csv("single_col.csv", content)

    schema = infer_schema(csv_path, sample_rows=10)

    assert len(schema) == 1, "Should have exactly one column"
    assert schema[0]['name'] == 'name', "Column name should be 'name'"


def test_header_only_csv(create_temp_csv):
    """Test schema inference for header-only CSV.

    Given: A CSV file with only headers (no data rows)
    When: Schema inference is performed
    Then: Should return empty schema (no data to infer from)
    """
    content = "id,name,age"
    csv_path = create_temp_csv("header_only.csv", content)

    schema = infer_schema(csv_path, sample_rows=10)

    # Current implementation returns empty schema for header-only CSV
    # This is acceptable as there's no data to infer types from
    assert len(schema) == 0, "Should return empty schema for header-only CSV"


def test_special_characters_in_column_names(create_temp_csv):
    """Test handling of special characters in column names.

    Given: A CSV file with special characters in column names
    When: Schema inference is performed
    Then: Column names should be cleaned properly
    """
    content = "id,user_name,first-name\n1,john_doe,Alice"
    csv_path = create_temp_csv("special_chars.csv", content)

    schema = infer_schema(csv_path, sample_rows=10)

    # Check that column names are preserved
    column_names = [col['name'] for col in schema]
    assert 'user_name' in column_names, "Should preserve underscores"


# ========================================================================
#  Performance Tests
# ========================================================================

def test_large_sample_size(create_temp_csv):
    """Test type inference with large sample size.

    Given: A CSV file with 10000 rows
    When: Schema inference is performed with sample_rows=5000
    Then: Should complete without errors and use sample for inference
    """
    # Create CSV with 10000 rows
    rows = ["id,value\n"]
    for i in range(10000):
        rows.append(f"{i},{i * 1.5}\n")

    content = "".join(rows)
    csv_path = create_temp_csv("large_file.csv", content)

    schema = infer_schema(csv_path, sample_rows=5000)

    assert len(schema) == 2, "Should have two columns"
    id_col = next((col for col in schema if col['name'] == 'id'), None)
    assert id_col['type'] == 'Integer', "Should infer Integer for id column"
