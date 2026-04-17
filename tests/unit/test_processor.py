"""
Unit tests for Enhanced Processor

Tests the enhanced Processor class that integrates:
- Plugin system
- Configuration-driven behavior
- All connectors (CSV, PostgreSQL, MySQL, API)
- Streaming support
- Backward compatibility with existing data-processor.py functionality
"""

import pytest
import tempfile
import json
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import Mock, patch, MagicMock, call
import duckdb
import pandas as pd

from src.core.processor import Processor
from src.core.plugins import PluginRegistry, Plugin
from src.core.config.loader import Config
from src.core.database import DatabaseConnection
from src.core.connectors import CSVConnector


# ========================================================================
#  Test Fixtures
# ========================================================================

@pytest.fixture
def sample_csv_file():
    """Create a sample CSV file for testing"""
    csv_data = """id,name,age,amount,region,status
1,Alice,30,1500.50,North,active
2,Bob,25,950.75,South,active
3,Charlie,35,2500.00,East,inactive
4,Diana,28,1800.00,West,active
5,Eve,32,2200.50,North,active
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(csv_data)
        temp_path = f.name

    yield temp_path

    # Cleanup
    Path(temp_path).unlink(missing_ok=True)


@pytest.fixture
def sample_csv_with_kv():
    """Create a CSV file with key:value format"""
    csv_data = """1,age:30,region:North,amount:1500,2023-01-15
2,age:25,region:South,amount:950,2023-02-20
3,age:35,region:East,amount:2500,2023-03-10
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(csv_data)
        temp_path = f.name

    yield temp_path

    Path(temp_path).unlink(missing_ok=True)


@pytest.fixture
def mock_config():
    """Create a mock configuration object"""
    config = Mock(spec=Config)
    config.processor = Mock()
    config.processor.default_connector = "csv"
    config.processor.max_memory_mb = 512
    config.processor.streaming_threshold_mb = 100
    config.processor.plugins = Mock()
    config.processor.plugins.enabled = True
    config.processor.plugins.auto_load = False
    config.processor.export = Mock()
    config.processor.export.default_format = "csv"
    config.processor.export.include_headers = True
    return config


@pytest.fixture
def mock_plugin_registry():
    """Create a mock plugin registry"""
    registry = Mock(spec=PluginRegistry)
    registry.get_enabled_plugins.return_value = []
    registry.load_plugins.return_value = None
    return registry


@pytest.fixture
def mock_database():
    """Create a mock database connection"""
    db = Mock(spec=DatabaseConnection)
    db.execute.return_value = []
    db.is_connected = True
    return db


@pytest.fixture
def real_duckdb_connection():
    """Create a real DuckDB in-memory connection for integration tests"""
    con = duckdb.connect(':memory:')
    yield con
    con.close()


# ========================================================================
#  Processor Initialization Tests
# ========================================================================

class TestProcessorInitialization:
    """Test Processor initialization and configuration"""

    def test_init_with_config_path(self, tmp_path):
        """Test initialization with config file path"""
        # Create a temporary config file
        config_content = """
processor:
  default_connector: "csv"
  max_memory_mb: 512
  streaming_threshold_mb: 100
  plugins:
    enabled: true
    auto_load: false
  export:
    default_format: "csv"
    include_headers: true
"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(config_content)

        # This should fail because Processor doesn't exist yet
        with pytest.raises(ImportError):
            processor = Processor(config_path=str(config_file))

    def test_init_with_config_object(self, mock_config):
        """Test initialization with Config object"""
        with pytest.raises(ImportError):
            processor = Processor(config=mock_config)

    def test_init_with_duckdb_connection(self, real_duckdb_connection):
        """Test initialization with existing DuckDB connection"""
        with pytest.raises(ImportError):
            processor = Processor(connection=real_duckdb_connection)

    def test_init_default_parameters(self):
        """Test initialization with default parameters"""
        with pytest.raises(ImportError):
            processor = Processor()


# ========================================================================
#  Data Loading Tests - CSV
# ========================================================================

class TestProcessorLoadCSV:
    """Test CSV loading functionality"""

    def test_load_csv_file(self, sample_csv_file):
        """Test loading CSV file into processor"""
        with pytest.raises((ImportError, AttributeError)):
            processor = Processor()
            processor.load_csv(sample_csv_file)

    def test_load_csv_with_custom_options(self, sample_csv_file):
        """Test loading CSV with custom delimiter and encoding"""
        with pytest.raises((ImportError, AttributeError)):
            processor = Processor()
            processor.load_csv(
                sample_csv_file,
                delimiter=',',
                has_header=True,
                encoding='utf-8'
            )

    def test_load_csv_into_table(self, sample_csv_file):
        """Test loading CSV into specific table"""
        with pytest.raises((ImportError, AttributeError)):
            processor = Processor()
            processor.load_csv(sample_csv_file, table_name='custom_data')

    def test_load_csv_with_schema_inference(self, sample_csv_file):
        """Test that CSV loading infers column types"""
        with pytest.raises((ImportError, AttributeError)):
            processor = Processor()
            processor.load_csv(sample_csv_file)
            # Should have inferred schema
            schema = processor.schema()
            assert 'id' in schema
            assert 'name' in schema


# ========================================================================
#  Data Loading Tests - Database
# ========================================================================

class TestProcessorLoadDatabase:
    """Test database loading functionality"""

    def test_load_from_postgresql(self):
        """Test loading data from PostgreSQL database"""
        with pytest.raises((ImportError, AttributeError)):
            processor = Processor()
            processor.load_database(
                connection_string="postgresql://user:pass@host:5432/db",
                query="SELECT * FROM users"
            )

    def test_load_from_mysql(self):
        """Test loading data from MySQL database"""
        with pytest.raises((ImportError, AttributeError)):
            processor = Processor()
            processor.load_database(
                connection_string="mysql://user:pass@host:3306/db",
                query="SELECT * FROM products"
            )

    def test_load_from_duckdb_query(self, real_duckdb_connection):
        """Test loading data from DuckDB query"""
        with pytest.raises((ImportError, AttributeError)):
            processor = Processor()
            processor.load_database(
                connection=real_duckdb_connection,
                query="SELECT 1 as value"
            )


# ========================================================================
#  Data Loading Tests - API
# ========================================================================

class TestProcessorLoadAPI:
    """Test API loading functionality"""

    def test_load_from_api_endpoint(self):
        """Test loading data from REST API endpoint"""
        with pytest.raises((ImportError, AttributeError)):
            processor = Processor()
            processor.load_api(
                url="https://api.example.com/data",
                method="GET"
            )

    def test_load_from_api_with_authentication(self):
        """Test loading data from API with auth headers"""
        with pytest.raises((ImportError, AttributeError)):
            processor = Processor()
            processor.load_api(
                url="https://api.example.com/secure-data",
                headers={"Authorization": "Bearer token123"}
            )

    def test_load_from_api_with_pagination(self):
        """Test loading data from paginated API"""
        with pytest.raises((ImportError, AttributeError)):
            processor = Processor()
            processor.load_api(
                url="https://api.example.com/paginated",
                paginate=True,
                page_size=100
            )


# ========================================================================
#  Data Processing Tests - Filter
# ========================================================================

class TestProcessorFilter:
    """Test data filtering functionality"""

    def test_filter_with_where_clause(self, sample_csv_file):
        """Test filtering data with WHERE clause"""
        with pytest.raises((ImportError, AttributeError)):
            processor = Processor()
            processor.load_csv(sample_csv_file)
            result = processor.filter("status = 'active'")
            assert len(result) == 4  # 4 active records

    def test_filter_with_multiple_conditions(self, sample_csv_file):
        """Test filtering with multiple conditions"""
        with pytest.raises((ImportError, AttributeError)):
            processor = Processor()
            processor.load_csv(sample_csv_file)
            result = processor.filter(
                "status = 'active' AND CAST(amount AS DOUBLE) >= 1500"
            )
            assert len(result) == 3

    def test_create_filtered_view(self, sample_csv_file):
        """Test creating a persistent filtered view"""
        with pytest.raises((ImportError, AttributeError)):
            processor = Processor()
            processor.load_csv(sample_csv_file)
            processor.create_view('active_users', "status = 'active'")
            # View should be queryable
            result = processor.sql("SELECT * FROM active_users")
            assert len(result) == 4


# ========================================================================
#  Data Processing Tests - Transform
# ========================================================================

class TestProcessorTransform:
    """Test data transformation functionality"""

    def test_add_derived_column(self, sample_csv_file):
        """Test adding a derived column with SQL expression"""
        with pytest.raises((ImportError, AttributeError)):
            processor = Processor()
            processor.load_csv(sample_csv_file)
            processor.add_column('tier', """
                CASE
                    WHEN CAST(amount AS DOUBLE) >= 2000 THEN 'GOLD'
                    WHEN CAST(amount AS DOUBLE) >= 1000 THEN 'SILVER'
                    ELSE 'BRONZE'
                END
            """)
            schema = processor.schema()
            assert 'tier' in schema

    def test_transform_with_lambda(self, sample_csv_file):
        """Test transforming column with Python lambda"""
        with pytest.raises((ImportError, AttributeError)):
            processor = Processor()
            processor.load_csv(sample_csv_file)
            processor.transform('name', lambda x: x.upper())
            result = processor.preview(1)
            assert result['name'][0] == 'ALICE'

    def test_transform_multiple_columns(self, sample_csv_file):
        """Test transforming multiple columns"""
        with pytest.raises((ImportError, AttributeError)):
            processor = Processor()
            processor.load_csv(sample_csv_file)
            processor.transform({
                'name': lambda x: x.upper(),
                'region': lambda x: x.lower()
            })


# ========================================================================
#  Data Processing Tests - Aggregate
# ========================================================================

class TestProcessorAggregate:
    """Test data aggregation functionality"""

    def test_aggregate_sum(self, sample_csv_file):
        """Test SUM aggregation"""
        processor = Processor()
        processor.load_csv(sample_csv_file)
        result = processor.aggregate('region', 'amount', 'SUM')
        assert len(result) == 4  # 4 regions
        assert 'sum_amount' in result.columns
        # Verify the aggregation worked correctly
        total_sum = result['sum_amount'].sum()
        assert total_sum > 0

    def test_aggregate_avg(self, sample_csv_file):
        """Test AVG aggregation"""
        processor = Processor()
        processor.load_csv(sample_csv_file)
        result = processor.aggregate('region', 'amount', 'AVG')
        assert len(result) == 4  # 4 regions
        assert 'avg_amount' in result.columns

    def test_aggregate_count(self, sample_csv_file):
        """Test COUNT aggregation"""
        processor = Processor()
        processor.load_csv(sample_csv_file)
        result = processor.aggregate('region', 'id', 'COUNT')
        assert len(result) == 4  # 4 regions
        assert 'count' in result.columns

    def test_aggregate_with_multiple_group_by(self, sample_csv_file):
        """Test aggregation with multiple GROUP BY columns"""
        processor = Processor()
        processor.load_csv(sample_csv_file)
        # For multiple group by, pass them as a list
        result = processor.aggregate(['region', 'name'], 'amount', 'SUM')
        assert len(result) > 0
        processor.add_column('tier', """
            CASE
                WHEN CAST(amount AS DOUBLE) >= 2000 THEN 'GOLD'
                ELSE 'SILVER'
            END
        """)
        result = processor.aggregate(
            ['region', 'tier'],
            'amount',
            'SUM'
        )


# ========================================================================
#  Data Processing Tests - Join
# ========================================================================

class TestProcessorJoin:
    """Test dataset joining functionality"""

    def test_join_two_datasets(self, sample_csv_file):
        """Test joining two loaded datasets"""
        # Create second CSV file
        csv_data2 = """region,manager
North,John
South,Jane
East,Bob
West,Alice
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_data2)
            temp_path2 = f.name

        try:
            with pytest.raises((ImportError, AttributeError)):
                processor = Processor()
                processor.load_csv(sample_csv_file, table_name='sales')
                processor.load_csv(temp_path2, table_name='regions')
                result = processor.join(
                    'sales', 'regions',
                    on='region',
                    how='LEFT'
                )
        finally:
            Path(temp_path2).unlink(missing_ok=True)


# ========================================================================
#  Export Tests
# ========================================================================

class TestProcessorExport:
    """Test data export functionality"""

    def test_export_to_csv(self, sample_csv_file, tmp_path):
        """Test exporting data to CSV file"""
        output_path = tmp_path / "output.csv"
        with pytest.raises((ImportError, AttributeError)):
            processor = Processor()
            processor.load_csv(sample_csv_file)
            processor.export_csv(str(output_path))
            assert output_path.exists()

    def test_export_to_json(self, sample_csv_file, tmp_path):
        """Test exporting data to JSON file"""
        output_path = tmp_path / "output.json"
        processor = Processor()
        processor.load_csv(sample_csv_file)
        processor.export_json(str(output_path))
        assert output_path.exists()
        # Verify JSON structure
        with open(output_path) as f:
            data = json.load(f)
            assert isinstance(data, list)

    def test_export_to_parquet(self, sample_csv_file, tmp_path):
        """Test exporting data to Parquet file"""
        output_path = tmp_path / "output.parquet"
        processor = Processor()
        processor.load_csv(sample_csv_file)
        processor.export_parquet(str(output_path))
        assert output_path.exists()

    def test_export_to_duckdb(self, sample_csv_file, tmp_path):
        """Test exporting data to DuckDB database"""
        output_path = tmp_path / "output.duckdb"
        processor = Processor()
        processor.load_csv(sample_csv_file)
        processor.export_duckdb(str(output_path), table_name='exported_data')
        assert output_path.exists()

    def test_export_query_result(self, sample_csv_file, tmp_path):
        """Test exporting query result instead of full table"""
        output_path = tmp_path / "filtered.csv"
        with pytest.raises((ImportError, AttributeError)):
            processor = Processor()
            processor.load_csv(sample_csv_file)
            processor.export_csv(
                str(output_path),
                query="SELECT * FROM data WHERE status = 'active'"
            )


# ========================================================================
#  Plugin Integration Tests
# ========================================================================

class TestProcessorPluginIntegration:
    """Test plugin system integration"""

    def test_load_plugins_on_init(self, mock_config, mock_plugin_registry):
        """Test that plugins are loaded during initialization"""
        with pytest.raises((ImportError, AttributeError)):
            processor = Processor(config=mock_config)
            # Plugin registry should be initialized
            assert processor.plugin_registry is not None

    def test_plugin_hook_on_load(self, mock_config):
        """Test plugin on_processor_load hook is called"""
        with pytest.raises((ImportError, AttributeError)):
            # Create a mock plugin that extends processor
            mock_plugin = Mock(spec=Plugin)
            mock_plugin.name = "test_plugin"
            mock_plugin.on_processor_load = Mock()

            processor = Processor(config=mock_config)
            processor.plugin_registry.register(mock_plugin)
            processor.plugin_registry.enable_plugin("test_plugin")

            # Hook should have been called
            mock_plugin.on_processor_load.assert_called_once_with(processor)

    def test_plugin_adds_custom_operation(self, mock_config):
        """Test that plugin can add custom operations to processor"""
        with pytest.raises((ImportError, AttributeError)):
            processor = Processor(config=mock_config)

            # Plugin should be able to extend processor
            class CustomPlugin(BasePlugin):
                def on_processor_load(self, processor):
                    processor.custom_operation = lambda: "custom_result"

            plugin = CustomPlugin(name="custom_ops")
            processor.plugin_registry.register(plugin)
            processor.plugin_registry.enable_plugin("custom_ops")

            # Custom operation should be available
            assert hasattr(processor, 'custom_operation')
            assert processor.custom_operation() == "custom_result"


# ========================================================================
#  Configuration Tests
# ========================================================================

class TestProcessorConfiguration:
    """Test configuration-driven behavior"""

    def test_default_connector_from_config(self, mock_config):
        """Test that default connector is loaded from config"""
        with pytest.raises((ImportError, AttributeError)):
            processor = Processor(config=mock_config)
            assert processor.default_connector == "csv"

    def test_memory_limit_from_config(self, mock_config):
        """Test that memory limit is set from config"""
        with pytest.raises((ImportError, AttributeError)):
            processor = Processor(config=mock_config)
            assert processor.max_memory_mb == 512

    def test_streaming_threshold_from_config(self, mock_config):
        """Test that streaming threshold is set from config"""
        with pytest.raises((ImportError, AttributeError)):
            processor = Processor(config=mock_config)
            assert processor.streaming_threshold_mb == 100

    def test_export_settings_from_config(self, mock_config):
        """Test that export settings are applied from config"""
        with pytest.raises((ImportError, AttributeError)):
            processor = Processor(config=mock_config)
            assert processor.export_format == "csv"
            assert processor.include_headers is True


# ========================================================================
#  Streaming Tests
# ========================================================================

class TestProcessorStreaming:
    """Test streaming functionality for large datasets"""

    def test_auto_streaming_for_large_file(self, tmp_path):
        """Test that large files automatically trigger streaming"""
        # Create a large CSV file (> 100MB equivalent in rows)
        csv_path = tmp_path / "large.csv"
        with open(csv_path, 'w') as f:
            f.write("id,value,category\n")
            for i in range(100000):  # Large number of rows
                f.write(f"{i},{i * 100.5},cat_{i % 100}\n")

        with pytest.raises((ImportError, AttributeError)):
            processor = Processor(streaming_threshold_mb=10)  # Low threshold to trigger
            # Should use streaming automatically
            processor.load_csv(str(csv_path))

    def test_stream_with_progress_callback(self, sample_csv_file):
        """Test streaming with progress reporting"""
        progress_updates = []

        def progress_callback(progress: Dict[str, Any]):
            progress_updates.append(progress)

        with pytest.raises((ImportError, AttributeError)):
            processor = Processor()
            processor.load_csv(sample_csv_file)
            # Stream query results with callback
            list(processor.stream_query(
                "SELECT * FROM data",
                progress_callback=progress_callback
            ))
            assert len(progress_updates) > 0

    def test_pause_resume_streaming(self, sample_csv_file):
        """Test pause and resume during streaming"""
        with pytest.raises((ImportError, AttributeError)):
            processor = Processor()
            processor.load_csv(sample_csv_file)

            stream = processor.stream_query("SELECT * FROM data")
            next(stream)  # Get first chunk
            processor.pause_stream()
            assert processor.is_stream_paused()
            processor.resume_stream()
            assert not processor.is_stream_paused()

    def test_cancel_streaming(self, sample_csv_file):
        """Test cancelling streaming operation"""
        with pytest.raises((ImportError, AttributeError)):
            processor = Processor()
            processor.load_csv(sample_csv_file)

            stream = processor.stream_query("SELECT * FROM data")
            next(stream)
            processor.cancel_stream()
            assert processor.is_stream_cancelled()


# ========================================================================
#  SQL Query Tests
# ========================================================================

class TestProcessorSQL:
    """Test SQL query functionality"""

    def test_execute_adhoc_sql(self, sample_csv_file):
        """Test executing ad-hoc SQL queries"""
        with pytest.raises((ImportError, AttributeError)):
            processor = Processor()
            processor.load_csv(sample_csv_file)
            result = processor.sql("SELECT COUNT(*) as cnt FROM data")
            assert result['cnt'][0] == 5

    def test_parameterized_query(self, sample_csv_file):
        """Test parameterized queries for SQL injection prevention"""
        with pytest.raises((ImportError, AttributeError)):
            processor = Processor()
            processor.load_csv(sample_csv_file)
            result = processor.sql(
                "SELECT * FROM data WHERE region = ?",
                parameters=['North']
            )
            assert len(result) == 2  # 2 records in North region

    def test_query_result_caching(self, sample_csv_file):
        """Test that identical queries are cached"""
        with pytest.raises((ImportError, AttributeError)):
            processor = Processor(cache_enabled=True)
            processor.load_csv(sample_csv_file)

            # Execute same query twice
            result1 = processor.sql("SELECT * FROM data WHERE region = 'North'")
            result2 = processor.sql("SELECT * FROM data WHERE region = 'North'")

            # Second query should be from cache
            assert processor.cache_hits > 0


# ========================================================================
#  Backward Compatibility Tests
# ========================================================================

class TestProcessorBackwardCompatibility:
    """Test backward compatibility with data-processor.py"""

    def test_preview_method(self, sample_csv_file):
        """Test preview method exists and works"""
        with pytest.raises((ImportError, AttributeError)):
            processor = Processor()
            processor.load_csv(sample_csv_file)
            result = processor.preview(3)
            assert len(result) == 3

    def test_schema_method(self, sample_csv_file):
        """Test schema method exists and works"""
        with pytest.raises((ImportError, AttributeError)):
            processor = Processor()
            processor.load_csv(sample_csv_file)
            schema = processor.schema()
            assert 'id' in schema
            assert 'name' in schema

    def test_coverage_method(self, sample_csv_file):
        """Test coverage method exists and works"""
        with pytest.raises((ImportError, AttributeError)):
            processor = Processor()
            processor.load_csv(sample_csv_file)
            coverage = processor.coverage()
            assert 'column' in coverage
            assert 'coverage_%' in coverage

    def test_pivot_method(self, sample_csv_file):
        """Test pivot method exists and works"""
        with pytest.raises((ImportError, AttributeError)):
            processor = Processor()
            processor.load_csv(sample_csv_file)
            processor.add_column('tier', """
                CASE
                    WHEN CAST(amount AS DOUBLE) >= 2000 THEN 'GOLD'
                    ELSE 'SILVER'
                END
            """)
            result = processor.pivot('region', 'tier', 'amount', 'SUM')
            assert 'region' in result


# ========================================================================
#  Error Handling Tests
# ========================================================================

class TestProcessorErrorHandling:
    """Test error handling and validation"""

    def test_invalid_csv_file(self):
        """Test handling of non-existent CSV file"""
        with pytest.raises((ImportError, AttributeError, FileNotFoundError)):
            processor = Processor()
            processor.load_csv('/nonexistent/file.csv')

    def test_invalid_sql_query(self, sample_csv_file):
        """Test handling of invalid SQL query"""
        with pytest.raises((ImportError, AttributeError)):
            processor = Processor()
            processor.load_csv(sample_csv_file)
            processor.sql("SELECT * FROM nonexistent_table")

    def test_memory_limit_exceeded(self, tmp_path):
        """Test handling when memory limit is exceeded"""
        # Create a file that would exceed small memory limit
        csv_path = tmp_path / "big.csv"
        with open(csv_path, 'w') as f:
            f.write("id,data\n")
            for i in range(10000):
                f.write(f"{i},{'x' * 1000}\n")  # Large data

        with pytest.raises((ImportError, AttributeError, MemoryError)):
            processor = Processor(max_memory_mb=1)  # Very small limit
            processor.load_csv(str(csv_path))

    def test_plugin_failure_graceful_degradation(self, mock_config):
        """Test that plugin failures don't crash processor"""
        with pytest.raises((ImportError, AttributeError)):
            # Create a plugin that will fail
            failing_plugin = Mock(spec=BasePlugin)
            failing_plugin.name = "failing_plugin"
            failing_plugin.on_processor_load.side_effect = Exception("Plugin error")

            processor = Processor(config=mock_config)
            processor.plugin_registry.register(failing_plugin)

            # Should handle plugin failure gracefully
            try:
                processor.plugin_registry.enable_plugin("failing_plugin")
            except Exception:
                pass  # Expected

            # Processor should still be functional
            assert processor is not None


# ========================================================================
#  Statistics and Metadata Tests
# ========================================================================

class TestProcessorStatistics:
    """Test statistics and metadata functionality"""

    def test_get_table_statistics(self, sample_csv_file):
        """Test getting statistics about loaded data"""
        with pytest.raises((ImportError, AttributeError)):
            processor = Processor()
            processor.load_csv(sample_csv_file)
            stats = processor.get_statistics()
            assert 'row_count' in stats
            assert 'column_count' in stats
            assert stats['row_count'] == 5

    def test_get_query_history(self, sample_csv_file):
        """Test query history tracking"""
        with pytest.raises((ImportError, AttributeError)):
            processor = Processor(track_queries=True)
            processor.load_csv(sample_csv_file)
            processor.sql("SELECT * FROM data")
            processor.sql("SELECT COUNT(*) FROM data")

            history = processor.get_query_history()
            assert len(history) >= 2

    def test_get_execution_plan(self, sample_csv_file):
        """Test getting query execution plan"""
        with pytest.raises((ImportError, AttributeError)):
            processor = Processor()
            processor.load_csv(sample_csv_file)
            plan = processor.explain("SELECT * FROM data WHERE region = 'North'")
            assert plan is not None
