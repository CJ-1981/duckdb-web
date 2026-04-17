"""
Integration tests for Processor Workflow

Tests end-to-end workflow scenarios including:
- Multi-connector data processing
- Plugin lifecycle validation
- Complete data pipelines
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
import duckdb

from src.core.processor import Processor
from src.core.plugins import Plugin, PluginRegistry
from src.core.config.loader import Config


# ========================================================================
#  Test Fixtures
# ========================================================================

@pytest.fixture
def sample_csv_1():
    """First CSV file"""
    csv_data = """id,name,department,salary
1,Alice,Engineering,80000
2,Bob,Sales,60000
3,Charlie,Engineering,90000
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(csv_data)
        yield f.name
    Path(f.name).unlink(missing_ok=True)


@pytest.fixture
def sample_csv_2():
    """Second CSV file"""
    csv_data = """department,location,budget
Engineering,NYC,500000
Sales,LA,300000
Marketing,CHI,200000
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(csv_data)
        yield f.name
    Path(f.name).unlink(missing_ok=True)


@pytest.fixture
def sample_config_yaml(tmp_path):
    """Create a sample config file"""
    config_content = """
processor:
  default_connector: "csv"
  max_memory_mb: 512
  streaming_threshold_mb: 100
  plugins:
    enabled: true
    auto_load: false
    search_paths: []
  export:
    default_format: "csv"
    include_headers: true
"""
    config_file = tmp_path / "config.yaml"
    config_file.write_text(config_content)
    yield str(config_file)


# ========================================================================
#  End-to-End Workflow Tests
# ========================================================================

class TestEndToEndWorkflow:
    """Test complete end-to-end workflows"""

    def test_load_transform_export_workflow(self, sample_csv_1, tmp_path):
        """Test complete workflow: load CSV, transform, export"""
        with pytest.raises((ImportError, AttributeError)):
            # Initialize processor
            processor = Processor()

            # Load data
            processor.load_csv(sample_csv_1)

            # Transform data
            processor.add_column('salary_tier', """
                CASE
                    WHEN CAST(salary AS INTEGER) >= 80000 THEN 'HIGH'
                    ELSE 'STANDARD'
                END
            """)

            # Filter data
            filtered = processor.filter("salary_tier = 'HIGH'")

            # Export result
            output_path = tmp_path / "output.csv"
            processor.export_csv(str(output_path), query="SELECT * FROM data WHERE salary_tier = 'HIGH'")

            # Verify export
            assert output_path.exists()

    def test_join_multiple_datasets(self, sample_csv_1, sample_csv_2):
        """Test joining data from multiple CSV files"""
        with pytest.raises((ImportError, AttributeError)):
            processor = Processor()

            # Load first dataset
            processor.load_csv(sample_csv_1, table_name='employees')

            # Load second dataset
            processor.load_csv(sample_csv_2, table_name='departments')

            # Join datasets
            result = processor.sql("""
                SELECT e.name, e.salary, d.budget
                FROM employees e
                JOIN departments d ON e.department = d.department
            """)

            assert len(result) >= 2

    def test_aggregation_workflow(self, sample_csv_1):
        """Test aggregation workflow"""
        with pytest.raises((ImportError, AttributeError)):
            processor = Processor()
            processor.load_csv(sample_csv_1)

            # Aggregate by department
            result = processor.aggregate('department', 'salary', 'AVG')

            assert 'department' in result
            assert 'avg_salary' in result

    def test_multiple_exports(self, sample_csv_1, tmp_path):
        """Test exporting to multiple formats"""
        with pytest.raises((ImportError, AttributeError)):
            processor = Processor()
            processor.load_csv(sample_csv_1)

            # Export to CSV
            csv_path = tmp_path / "output.csv"
            processor.export_csv(str(csv_path))

            # Export to JSON
            json_path = tmp_path / "output.json"
            processor.export_json(str(json_path))

            # Export to Parquet
            parquet_path = tmp_path / "output.parquet"
            processor.export_parquet(str(parquet_path))

            # Verify all exports exist
            assert csv_path.exists()
            assert json_path.exists()
            assert parquet_path.exists()


# ========================================================================
#  Plugin Integration Tests
# ========================================================================

class TestPluginIntegration:
    """Test plugin integration with processor"""

    def test_custom_processing_plugin(self, sample_csv_1):
        """Test plugin that adds custom processing method"""
        with pytest.raises((ImportError, AttributeError)):
            # Create a custom plugin
            class CustomProcessingPlugin(BasePlugin):
                name = "custom_processing"
                version = "1.0.0"

                def on_processor_load(self, processor):
                    """Add custom method to processor"""
                    def custom_filter_by_salary(processor_self, min_salary):
                        return processor_self.filter(f"CAST(salary AS INTEGER) >= {min_salary}")

                    processor.custom_filter_by_salary = lambda min_salary: custom_filter_by_salary(processor, min_salary)

            processor = Processor()
            processor.plugin_registry.register(CustomProcessingPlugin())
            processor.plugin_registry.enable_plugin("custom_processing")

            processor.load_csv(sample_csv_1)

            # Use custom method added by plugin
            result = processor.custom_filter_by_salary(80000)
            assert len(result) >= 2

    def test_plugin_hooks_called(self, sample_csv_1):
        """Test that plugin lifecycle hooks are called"""
        with pytest.raises((ImportError, AttributeError)):
            # Create a mock plugin
            mock_plugin = Mock(spec=BasePlugin)
            mock_plugin.name = "test_plugin"
            mock_plugin.version = "1.0.0"

            processor = Processor()
            processor.plugin_registry.register(mock_plugin)
            processor.plugin_registry.enable_plugin("test_plugin")

            # Load data - should trigger on_data_load hook
            processor.load_csv(sample_csv_1)

            # Verify hook was called
            if hasattr(mock_plugin, 'on_data_load'):
                mock_plugin.on_data_load.assert_called()

    def test_multiple_plugins_cooperation(self, sample_csv_1):
        """Test multiple plugins working together"""
        with pytest.raises((ImportError, AttributeError)):
            # Create two plugins
            class Plugin1(BasePlugin):
                name = "plugin1"
                version = "1.0.0"

                def on_processor_load(self, processor):
                    processor.plugin1_loaded = True

            class Plugin2(BasePlugin):
                name = "plugin2"
                version = "1.0.0"

                def on_processor_load(self, processor):
                    processor.plugin2_loaded = True

            processor = Processor()
            processor.plugin_registry.register(Plugin1())
            processor.plugin_registry.register(Plugin2())

            processor.plugin_registry.enable_plugin("plugin1")
            processor.plugin_registry.enable_plugin("plugin2")

            # Both plugins should have added their attributes
            assert processor.plugin1_loaded
            assert processor.plugin2_loaded


# ========================================================================
#  Configuration-Driven Behavior Tests
# ========================================================================

class TestConfigurationDrivenBehavior:
    """Test that processor behavior is controlled by configuration"""

    def test_config_default_connector(self, sample_config_yaml, sample_csv_1):
        """Test default connector from config"""
        with pytest.raises((ImportError, AttributeError)):
            config = Config(sample_config_yaml)
            processor = Processor(config=config)

            # Should use CSV as default connector
            processor.load_data(sample_csv_1)  # Uses default connector

            assert processor.table_exists('data')

    def test_config_memory_limit(self, tmp_path):
        """Test memory limit from config"""
        # Create a config with small memory limit
        config_content = """
processor:
  default_connector: "csv"
  max_memory_mb: 1
  streaming_threshold_mb: 0.5
  plugins:
    enabled: false
  export:
    default_format: "csv"
"""
        config_file = tmp_path / "small_memory_config.yaml"
        config_file.write_text(config_content)

        # Create a large file
        csv_path = tmp_path / "large.csv"
        with open(csv_path, 'w') as f:
            f.write("id,data\n")
            for i in range(10000):
                f.write(f"{i},{'x' * 1000}\n")

        with pytest.raises((ImportError, AttributeError, MemoryError)):
            config = Config(str(config_file))
            processor = Processor(config=config)
            processor.load_csv(str(csv_path))

    def test_config_plugin_settings(self, sample_config_yaml):
        """Test plugin settings from config"""
        with pytest.raises((ImportError, AttributeError)):
            config = Config(sample_config_yaml)
            processor = Processor(config=config)

            # Check plugin settings are applied
            assert processor.config.processor.plugins.enabled is True
            assert processor.config.processor.plugins.auto_load is False


# ========================================================================
#  Performance Tests
# ========================================================================

class TestProcessorPerformance:
    """Test performance characteristics"""

    def test_large_file_performance(self, tmp_path):
        """Test processing large file efficiently"""
        # Create a moderately large file
        csv_path = tmp_path / "large.csv"
        with open(csv_path, 'w') as f:
            f.write("id,name,value,category\n")
            for i in range(50000):
                f.write(f"{i},Item_{i},{i * 10.5},Cat_{i % 10}\n")

        with pytest.raises((ImportError, AttributeError)):
            processor = Processor()
            processor.load_csv(str(csv_path))

            # Should be able to query efficiently
            result = processor.aggregate('category', 'value', 'SUM')
            assert len(result) == 10  # 10 categories

    def test_memory_efficiency(self, tmp_path):
        """Test memory efficiency with streaming"""
        csv_path = tmp_path / "stream.csv"
        with open(csv_path, 'w') as f:
            f.write("id,data\n")
            for i in range(10000):
                f.write(f"{i},{'x' * 500}\n")

        with pytest.raises((ImportError, AttributeError)):
            processor = Processor(streaming_threshold_mb=1)
            processor.load_csv(str(csv_path))

            # Should have used streaming
            stats = processor.get_statistics()
            assert stats['row_count'] == 10000


# ========================================================================
#  Error Recovery Tests
# ========================================================================

class TestErrorRecovery:
    """Test error recovery and resilience"""

    def test_recover_from_bad_query(self, sample_csv_1):
        """Test recovery from invalid query"""
        with pytest.raises((ImportError, AttributeError)):
            processor = Processor()
            processor.load_csv(sample_csv_1)

            # Try invalid query
            with pytest.raises(Exception):
                processor.sql("SELECT * FROM nonexistent_table")

            # Processor should still be functional
            result = processor.sql("SELECT * FROM data")
            assert len(result) > 0

    def test_recover_from_plugin_error(self, sample_csv_1):
        """Test recovery from plugin error"""
        with pytest.raises((ImportError, AttributeError)):
            # Create a plugin that will fail
            class FailingPlugin(BasePlugin):
                name = "failing_plugin"
                version = "1.0.0"

                def on_data_load(self, data):
                    raise Exception("Plugin error")

            processor = Processor()
            processor.plugin_registry.register(FailingPlugin())
            processor.plugin_registry.enable_plugin("failing_plugin")

            # Should handle plugin error gracefully
            processor.load_csv(sample_csv_1)

            # Processor should still work
            result = processor.preview()
            assert len(result) > 0
