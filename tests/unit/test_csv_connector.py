"""
Unit tests for CSV Connector

Tests CSV connector functionality including:
- Automatic type inference
- Custom delimiters and headers
- Missing value handling
- Large file streaming
- Integration with DuckDB
"""

import pytest
import tempfile
import csv
from pathlib import Path
from typing import List, Dict, Any
from unittest.mock import Mock, patch, MagicMock

from src.core.connectors.csv import CSVConnector
from src.core.connectors.base import BaseConnector
from src.core.connectors import get_connector, register_connector, CONNECTOR_REGISTRY
from src.core.database import DatabaseConnection


# ========================================================================
#  Test Fixtures
# =========================================================================

@pytest.fixture
def sample_csv_data() -> str:
    """Sample CSV data with mixed types"""
    return """id,name,age,amount,active,join_date
1,Alice,30,1500.50,true,2023-01-15
2,Bob,25,950.75,false,2023-02-20
3,Charlie,35,2500.00,true,2023-03-10
"""


@pytest.fixture
def csv_with_custom_delimiter() -> str:
    """CSV data with pipe delimiter"""
    return """id|name|amount|region
1|Product A|100.50|North
2|Product B|250.75|South
3|Product C|75.25|East
"""


@pytest.fixture
def csv_with_missing_values() -> str:
    """CSV data with various missing value representations"""
    return """id,name,age,amount,status
1,Alice,30,1500.50,active
2,Bob,,,
3,Charlie,35,,inactive
4,,40,2500.00,
5,David,NA,1800.75,pending
"""


@pytest.fixture
def large_csv_file() -> tempfile._TemporaryFileWrapper:
    """Create a large CSV file (>100MB equivalent in rows)"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        writer = csv.writer(f)
        # Header
        writer.writerow(['id', 'name', 'value', 'timestamp', 'category'])
        # Write many rows (simulating large file)
        for i in range(10000):  # 10k rows for testing
            writer.writerow([i, f'Item_{i}', i * 100.5, f'2023-01-{i % 28 + 1}', f'Cat_{i % 5}'])
        temp_path = f.name
        f.flush()

    yield temp_path

    # Cleanup
    Path(temp_path).unlink(missing_ok=True)


@pytest.fixture
def mock_database():
    """Mock database connection"""
    db = Mock(spec=DatabaseConnection)
    db.execute.return_value = []
    return db


# ========================================================================
#  CSVConnector Class Tests
# ========================================================================

class TestCSVConnectorInitialization:
    """Test CSV connector initialization and configuration"""

    def test_init_with_defaults(self):
        """Test initialization with default parameters"""
        connector = CSVConnector()
        assert connector.delimiter == ','
        assert connector.has_header is True
        assert connector.encoding == 'utf-8'
        assert connector.streaming_threshold == 100 * 1024 * 1024  # 100MB
        assert connector.chunk_size == 10000

    def test_init_with_custom_delimiter(self):
        """Test initialization with custom delimiter"""
        connector = CSVConnector(delimiter='|')
        assert connector.delimiter == '|'

    def test_init_with_tab_delimiter(self):
        """Test initialization with tab delimiter"""
        connector = CSVConnector(delimiter='\t')
        assert connector.delimiter == '\t'

    def test_init_without_header(self):
        """Test initialization without header row"""
        connector = CSVConnector(has_header=False)
        assert connector.has_header is False

    def test_init_with_custom_encoding(self):
        """Test initialization with custom encoding"""
        connector = CSVConnector(encoding='latin-1')
        assert connector.encoding == 'latin-1'

    def test_init_with_custom_threshold(self):
        """Test initialization with custom streaming threshold"""
        connector = CSVConnector(streaming_threshold=50 * 1024 * 1024)
        assert connector.streaming_threshold == 50 * 1024 * 1024

    def test_init_with_custom_chunk_size(self):
        """Test initialization with custom chunk size"""
        connector = CSVConnector(chunk_size=5000)
        assert connector.chunk_size == 5000

    def test_init_with_invalid_delimiter(self):
        """Test initialization with invalid delimiter raises error"""
        with pytest.raises(ValueError, match="Delimiter must be a single character"):
            CSVConnector(delimiter='')


class TestCSVConnectorTypeInference:
    """Test automatic type inference for CSV columns"""

    def test_infer_integer_type(self, sample_csv_data):
        """Test inferring integer type"""
        connector = CSVConnector()
        inferred_type = connector._infer_type(['1', '2', '3', '100', '-5'])
        assert inferred_type == 'INTEGER'

    def test_infer_float_type(self, sample_csv_data):
        """Test inferring float type"""
        connector = CSVConnector()
        inferred_type = connector._infer_type(['1.5', '2.75', '3.99', '100.1'])
        assert inferred_type == 'FLOAT'

    def test_infer_boolean_type(self, sample_csv_data):
        """Test inferring boolean type"""
        connector = CSVConnector()
        inferred_type = connector._infer_type(['true', 'false', 'TRUE', 'FALSE', 'True', 'False'])
        assert inferred_type == 'BOOLEAN'

    def test_infer_date_type(self, sample_csv_data):
        """Test inferring date type"""
        connector = CSVConnector()
        inferred_type = connector._infer_type(['2023-01-15', '2023-02-20', '2023-03-10'])
        assert inferred_type == 'DATE'

    def test_infer_string_type(self, sample_csv_data):
        """Test inferring string type for mixed content"""
        connector = CSVConnector()
        inferred_type = connector._infer_type(['Alice', 'Bob', 'Charlie'])
        assert inferred_type == 'VARCHAR'

    def test_infer_type_with_empty_values(self, sample_csv_data):
        """Test type inference with empty values"""
        connector = CSVConnector()
        inferred_type = connector._infer_type(['1', '2', '', '4'])
        assert inferred_type == 'INTEGER'

    def test_infer_schema_from_csv(self, sample_csv_data):
        """Test inferring complete schema from CSV data"""
        connector = CSVConnector()
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(sample_csv_data)
            temp_path = f.name

        try:
            schema = connector.infer_schema(temp_path)
            assert 'id' in schema
            assert 'name' in schema
            assert 'age' in schema
            assert 'amount' in schema
            assert 'active' in schema
            assert 'join_date' in schema

            # Check type inference
            assert schema['id'] == 'INTEGER'
            assert schema['name'] == 'VARCHAR'
            assert schema['age'] in ('INTEGER', 'VARCHAR')  # Could be either
            assert schema['amount'] in ('FLOAT', 'VARCHAR')
            assert schema['active'] in ('BOOLEAN', 'VARCHAR')
            assert schema['join_date'] in ('DATE', 'VARCHAR')
        finally:
            Path(temp_path).unlink(missing_ok=True)


class TestCSVConnectorReading:
    """Test CSV file reading with various configurations"""

    def test_read_csv_with_header(self, sample_csv_data):
        """Test reading CSV with header row"""
        connector = CSVConnector()
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(sample_csv_data)
            temp_path = f.name

        try:
            rows = list(connector.read_csv(temp_path))
            assert len(rows) == 3  # 3 data rows
            assert rows[0]['id'] == '1'
            assert rows[0]['name'] == 'Alice'
            assert rows[1]['name'] == 'Bob'
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_read_csv_without_header(self, sample_csv_data):
        """Test reading CSV without header row"""
        connector = CSVConnector(has_header=False)
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(sample_csv_data)
            temp_path = f.name

        try:
            rows = list(connector.read_csv(temp_path))
            assert len(rows) == 4  # All 4 rows including header
            # First row should be treated as data
            assert rows[0]['col_0'] == 'id'
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_read_csv_with_custom_delimiter(self, csv_with_custom_delimiter):
        """Test reading CSV with pipe delimiter"""
        connector = CSVConnector(delimiter='|')
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_with_custom_delimiter)
            temp_path = f.name

        try:
            rows = list(connector.read_csv(temp_path))
            assert len(rows) == 3
            assert rows[0]['name'] == 'Product A'
            assert rows[1]['region'] == 'South'
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_read_csv_with_missing_values(self, csv_with_missing_values):
        """Test reading CSV with missing values"""
        connector = CSVConnector()
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_with_missing_values)
            temp_path = f.name

        try:
            rows = list(connector.read_csv(temp_path))
            assert len(rows) == 5

            # Row 2 has empty fields
            assert rows[1]['name'] == 'Bob'
            assert rows[1]['age'] == '' or rows[1]['age'] is None

            # Row 5 has 'NA' value
            assert rows[4]['name'] == 'David'
            assert rows[4]['age'] == 'NA'
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_read_csv_with_empty_file(self):
        """Test reading empty CSV file"""
        connector = CSVConnector()
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write('')
            temp_path = f.name

        try:
            rows = list(connector.read_csv(temp_path))
            assert len(rows) == 0
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_read_csv_with_different_encoding(self):
        """Test reading CSV with non-UTF8 encoding"""
        connector = CSVConnector(encoding='latin-1')
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False,
                                         encoding='latin-1') as f:
            f.write('id,name\n1,Café\n2,München\n')
            temp_path = f.name

        try:
            rows = list(connector.read_csv(temp_path))
            assert len(rows) == 2
            assert rows[0]['name'] == 'Café'
            assert rows[1]['name'] == 'München'
        finally:
            Path(temp_path).unlink(missing_ok=True)


class TestCSVConnectorStreaming:
    """Test large file streaming functionality"""

    def test_stream_large_file_in_chunks(self, large_csv_file):
        """Test streaming large CSV file in chunks"""
        connector = CSVConnector(streaming_threshold=1)  # Force streaming

        chunks = []
        for chunk in connector.stream_csv(large_csv_file):
            chunks.append(chunk)
            assert len(chunk) <= connector.chunk_size

        total_rows = sum(len(chunk) for chunk in chunks)
        assert total_rows == 10000  # All rows should be read

    def test_stream_csv_with_progress_callback(self, large_csv_file):
        """Test streaming with progress reporting"""
        connector = CSVConnector(streaming_threshold=1)

        progress_updates = []

        def progress_callback(progress: Dict[str, Any]):
            progress_updates.append(progress)

        list(connector.stream_csv(large_csv_file, progress_callback=progress_callback))

        # Should have received progress updates
        assert len(progress_updates) > 0

        # Check progress data structure
        last_update = progress_updates[-1]
        assert 'rows_processed' in last_update
        assert 'total_rows' in last_update
        assert 'percentage' in last_update

    def test_stream_csv_returns_iterator(self, large_csv_file):
        """Test that streaming returns an iterator"""
        connector = CSVConnector(streaming_threshold=1)

        result = connector.stream_csv(large_csv_file)
        assert hasattr(result, '__iter__')
        assert hasattr(result, '__next__')

    def test_regular_read_for_small_file(self, sample_csv_data):
        """Test that small files are read efficiently"""
        connector = CSVConnector()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(sample_csv_data)
            temp_path = f.name

        try:
            # Should read all data efficiently
            result = list(connector.read_csv(temp_path))
            assert len(result) == 3  # All 3 data rows
            assert result[0]['name'] == 'Alice'
        finally:
            Path(temp_path).unlink(missing_ok=True)


class TestCSVConnectorDuckDBIntegration:
    """Test integration with DuckDB database"""

    def test_import_csv_to_duckdb_table(self, sample_csv_data, mock_database):
        """Test importing CSV data into DuckDB table"""
        connector = CSVConnector()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(sample_csv_data)
            temp_path = f.name

        try:
            connector.import_to_duckdb(
                csv_path=temp_path,
                db_connection=mock_database,
                table_name='users'
            )

            # Verify table creation was called
            assert mock_database.execute.called
            calls = [str(call) for call in mock_database.execute.call_args_list]
            create_call = [c for c in calls if 'CREATE TABLE' in c]
            assert len(create_call) > 0

            # Verify inserts were called
            insert_calls = [c for c in calls if 'INSERT INTO' in c]
            assert len(insert_calls) >= 3  # At least 3 data rows

        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_import_with_schema_inference(self, sample_csv_data, mock_database):
        """Test importing CSV with automatic schema inference"""
        connector = CSVConnector()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(sample_csv_data)
            temp_path = f.name

        try:
            connector.import_to_duckdb(
                csv_path=temp_path,
                db_connection=mock_database,
                table_name='users'
            )

            # Check that proper column types were used
            calls = [str(call) for call in mock_database.execute.call_args_list]
            create_call = [c for c in calls if 'CREATE TABLE' in c][0]

            # Should have proper type definitions
            assert 'id' in create_call
            assert 'name' in create_call

        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_import_with_custom_table_name(self, sample_csv_data, mock_database):
        """Test importing CSV with custom table name"""
        connector = CSVConnector()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(sample_csv_data)
            temp_path = f.name

        try:
            connector.import_to_duckdb(
                csv_path=temp_path,
                db_connection=mock_database,
                table_name='custom_table'
            )

            calls = [str(call) for call in mock_database.execute.call_args_list]
            assert any('custom_table' in str(call) for call in calls)

        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_import_with_batch_inserts(self, large_csv_file, mock_database):
        """Test importing large CSV uses batch inserts"""
        connector = CSVConnector(chunk_size=1000)

        connector.import_to_duckdb(
            csv_path=large_csv_file,
            db_connection=mock_database,
            table_name='large_data'
        )

        # Should use batch inserts for efficiency
        calls = [str(call) for call in mock_database.execute.call_args_list]
        insert_calls = [c for c in calls if 'INSERT INTO' in c]

        # Should have multiple batch insert calls
        assert len(insert_calls) > 1


class TestCSVConnectorValidation:
    """Test CSV validation and error handling"""

    def test_validate_csv_file_exists(self):
        """Test validation with non-existent file"""
        connector = CSVConnector()

        with pytest.raises(FileNotFoundError):
            connector.validate_csv_path('/nonexistent/path/file.csv')

    def test_validate_csv_file_not_empty(self):
        """Test validation with empty file"""
        connector = CSVConnector()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write('')
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="Empty CSV file"):
                connector.validate_csv_path(temp_path)
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_validate_csv_file_readable(self, sample_csv_data):
        """Test validation with readable CSV file"""
        connector = CSVConnector()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(sample_csv_data)
            temp_path = f.name

        try:
            # Should not raise any exception
            result = connector.validate_csv_path(temp_path)
            assert result is True
        finally:
            Path(temp_path).unlink(missing_ok=True)


class TestCSVConnectorMissingValueHandling:
    """Test missing value handling in CSV data"""

    def test_handle_null_values(self):
        """Test handling NULL string values"""
        connector = CSVConnector()

        csv_data = """id,name,value
1,Item,100
2,Item,NULL
3,Item,200
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_data)
            temp_path = f.name

        try:
            rows = list(connector.read_csv(temp_path))
            assert rows[1]['value'] == 'NULL' or rows[1]['value'] is None
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_handle_empty_string_missing_values(self):
        """Test handling empty strings as missing values"""
        connector = CSVConnector()

        csv_data = """id,name,value
1,Item,100
2,,
3,Item,200
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_data)
            temp_path = f.name

        try:
            rows = list(connector.read_csv(temp_path))
            assert rows[1]['name'] == '' or rows[1]['name'] is None
            assert rows[1]['value'] == '' or rows[1]['value'] is None
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_handle_na_missing_values(self):
        """Test handling NA string values"""
        connector = CSVConnector()

        csv_data = """id,name,value
1,Item,100
2,Item,NA
3,Item,200
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_data)
            temp_path = f.name

        try:
            rows = list(connector.read_csv(temp_path))
            assert rows[1]['value'] == 'NA' or rows[1]['value'] is None
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_handle_nan_missing_values(self):
        """Test handling NaN string values"""
        connector = CSVConnector()

        csv_data = """id,name,value
1,Item,100
2,Item,NaN
3,Item,200
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_data)
            temp_path = f.name

        try:
            rows = list(connector.read_csv(temp_path))
            assert rows[1]['value'] in ('NaN', 'nan', None)
        finally:
            Path(temp_path).unlink(missing_ok=True)


class TestCSVConnectorConfiguration:
    """Test connector configuration from config system"""

    def test_configure_from_yaml(self):
        """Test loading connector configuration from YAML"""
        # Mock config object
        mock_config = Mock()
        mock_csv_config = Mock()
        mock_csv_config.delimiter = '|'
        mock_csv_config.has_header = False
        mock_csv_config.encoding = 'latin-1'
        mock_csv_config.streaming_threshold = 50000000
        mock_csv_config.chunk_size = 5000
        mock_config.connectors.csv = mock_csv_config

        connector = CSVConnector.from_config(mock_config)

        assert connector.delimiter == '|'
        assert connector.has_header is False
        assert connector.encoding == 'latin-1'
        assert connector.streaming_threshold == 50000000
        assert connector.chunk_size == 5000


class TestCSVConnectorStatistics:
    """Test CSV file statistics and metadata"""

    def test_get_csv_statistics(self, sample_csv_data):
        """Test getting statistics about CSV file"""
        connector = CSVConnector()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(sample_csv_data)
            temp_path = f.name

        try:
            stats = connector.get_statistics(temp_path)

            assert 'row_count' in stats
            assert 'column_count' in stats
            assert 'columns' in stats
            assert 'file_size' in stats

            assert stats['row_count'] == 3  # 3 data rows
            assert stats['column_count'] == 6  # 6 columns
            assert len(stats['columns']) == 6
            assert stats['file_size'] > 0

        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_get_statistics_for_empty_file(self):
        """Test statistics for empty file"""
        connector = CSVConnector()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write('')
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="Empty CSV file"):
                connector.get_statistics(temp_path)
        finally:
            Path(temp_path).unlink(missing_ok=True)


class TestConnectorRegistry:
    """Test connector registry functionality"""

    def test_get_connector_csv(self):
        """Test getting CSV connector from registry"""
        connector_class = get_connector('csv')
        assert connector_class == CSVConnector

    def test_get_connector_unknown_type(self):
        """Test getting unknown connector type raises error"""
        with pytest.raises(KeyError, match="Unknown connector type"):
            get_connector('unknown_type')

    def test_register_connector_invalid_class(self):
        """Test registering invalid connector class raises error"""
        class NotAConnector:
            pass

        with pytest.raises(TypeError, match="must inherit from BaseConnector"):
            register_connector('invalid', NotAConnector)

    def test_register_custom_connector(self):
        """Test registering a custom connector"""
        # Save original registry
        original_registry = CONNECTOR_REGISTRY.copy()

        try:
            class CustomConnector(BaseConnector):
                def connect(self, **kwargs):
                    pass

                def read(self, **kwargs):
                    yield {}

                def validate(self, **kwargs):
                    return True

                def get_metadata(self, **kwargs):
                    return {}

            # Register custom connector
            register_connector('custom', CustomConnector)

            # Verify it's registered
            connector_class = get_connector('custom')
            assert connector_class == CustomConnector
        finally:
            # Restore original registry
            CONNECTOR_REGISTRY.clear()
            CONNECTOR_REGISTRY.update(original_registry)
