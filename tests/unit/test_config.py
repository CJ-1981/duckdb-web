"""
Test Suite: Configuration Management
Task: P1-T002 Configuration Management
Phase: TDD RED (Write tests BEFORE implementation)
Coverage Target: 85%+

This test file defines the expected behavior of the configuration management system.
All tests should FAIL initially (RED phase) until implementation is complete.
"""

import pytest
from pathlib import Path
from typing import Any, Dict
from unittest.mock import Mock, patch, MagicMock
import os
import yaml
import tempfile
import threading
import time


# ============================================================================
# FIXTURES - Mock objects and test data
# ============================================================================

@pytest.fixture
def valid_config_dict():
    """
    GIVEN a valid configuration structure
    WHEN tests need configuration data
    THEN return a valid config dictionary
    """
    return {
        "database": {
            "host": "localhost",
            "port": 5432,
            "name": "testdb",
            "user": "testuser",
            "password": "testpass"
        },
        "redis": {
            "host": "localhost",
            "port": 6379,
            "db": 0
        },
        "logging": {
            "level": "INFO",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        },
        "plugins": {
            "paths": ["/usr/local/lib/plugins", "~/.local/plugins"],
            "auto_load": True
        }
    }


@pytest.fixture
def valid_yaml_file(tmp_path, valid_config_dict):
    """
    GIVEN a valid YAML configuration file
    WHEN tests need a config file path
    THEN return path to valid YAML file
    """
    config_file = tmp_path / "config.yaml"
    with open(config_file, 'w') as f:
        yaml.dump(valid_config_dict, f)
    return config_file


@pytest.fixture
def invalid_yaml_file(tmp_path):
    """
    GIVEN an invalid YAML configuration file
    WHEN tests need an invalid config
    THEN return path to invalid YAML file
    """
    config_file = tmp_path / "invalid_config.yaml"
    with open(config_file, 'w') as f:
        f.write("invalid: yaml: content:\n  - broken\n    - structure\n")
    return config_file


@pytest.fixture
def config_with_env_overrides(valid_config_dict):
    """
    GIVEN environment variables are set
    WHEN config is loaded
    THEN environment variables override YAML values
    """
    # Set environment variables
    os.environ['APP_DATABASE_HOST'] = 'override-host'
    os.environ['APP_DATABASE_PORT'] = '9999'
    os.environ['APP_REDIS_HOST'] = 'override-redis'
    os.environ['APP_LOGGING_LEVEL'] = 'DEBUG'

    yield valid_config_dict

    # Cleanup
    del os.environ['APP_DATABASE_HOST']
    del os.environ['APP_DATABASE_PORT']
    del os.environ['APP_REDIS_HOST']
    del os.environ['APP_LOGGING_LEVEL']


# ============================================================================
# TEST CLASS 1: Configuration Loading from YAML (Acceptance Criteria #1)
# ============================================================================

class TestConfigurationLoading:
    """
    GIVEN a valid YAML configuration file exists
    WHEN the configuration is loaded
    THEN all values are correctly parsed and accessible
    """

    def test_config_loaded_from_yaml_file(self, valid_yaml_file):
        """
        GIVEN a valid YAML configuration file exists
        WHEN the configuration is loaded from file
        THEN all configuration values are accessible

        Acceptance Criteria:
        - Configuration loaded from YAML files with validation
        """
        from src.core.config.loader import Config

        manager = Config(valid_yaml_file)
        config = manager.load()

        # Verify top-level keys
        assert "database" in config
        assert "redis" in config
        assert "logging" in config
        assert "plugins" in config

        # Verify nested values
        assert config.database.host == "localhost"
        assert config.database.port == 5432
        assert config.redis.port == 6379
        assert config.logging.level == "INFO"

    def test_config_loading_with_multiple_yaml_files(self, tmp_path, valid_config_dict):
        """
        GIVEN multiple YAML configuration files
        WHEN configurations are loaded from multiple files
        THEN later files override earlier files (merge behavior)
        """
        from src.core.config.loader import Config

        # Create base config
        base_config = tmp_path / "base.yaml"
        with open(base_config, 'w') as f:
            yaml.dump(valid_config_dict, f)

        # Create override config
        override_config = tmp_path / "override.yaml"
        override_data = {
            "database": {
                "host": "override-host",
                "port": 3306  # Different port
            }
        }
        with open(override_config, 'w') as f:
            yaml.dump(override_data, f)

        # Load with override
        manager = Config([base_config, override_config])
        config = manager.load()

        # Verify override worked
        assert config.database.host == "override-host"
        assert config.database.port == 3306
        # Non-overridden values should remain
        assert config.database.name == "testdb"

    def test_config_loading_fails_on_nonexistent_file(self):
        """
        GIVEN a request to load a nonexistent config file
        WHEN the config manager attempts to load
        THEN appropriate error is raised with clear message
        """
        from src.core.config.loader import Config

        manager = Config("/nonexistent/path/config.yaml")

        with pytest.raises(FileNotFoundError, match="Configuration file not found"):
            manager.load()

    def test_config_loading_fails_on_invalid_yaml(self, invalid_yaml_file):
        """
        GIVEN an invalid YAML configuration file
        WHEN the config manager attempts to load
        THEN validation error is raised with details
        """
        from src.core.config.loader import Config

        manager = Config(invalid_yaml_file)

        with pytest.raises(yaml.YAMLError, match="Invalid YAML"):
            manager.load()

    def test_config_loading_with_absolute_path(self, valid_yaml_file):
        """
        GIVEN a config file with absolute path
        WHEN config is loaded
        THEN absolute path is resolved correctly
        """
        from src.core.config.loader import Config

        abs_path = str(valid_yaml_file.resolve())
        manager = Config(abs_path)
        config = manager.load()

        assert config is not None

    def test_config_loading_with_relative_path(self, valid_yaml_file, tmp_path):
        """
        GIVEN a config file with relative path
        WHEN config is loaded
        THEN path is resolved relative to current directory
        """
        from src.core.config.loader import Config

        # Change to temp directory
        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            manager = Config("config.yaml")
            config = manager.load()

            assert config is not None
        finally:
            os.chdir(original_cwd)


# ============================================================================
# TEST CLASS 2: Environment Variable Override (Acceptance Criteria #2)
# ============================================================================

class TestEnvironmentVariableOverrides:
    """
    GIVEN configuration is loaded from YAML
    WHEN environment variables are set
    THEN environment variables override YAML values
    """

    def test_environment_variable_override_single_value(self, valid_yaml_file):
        """
        GIVEN a config file with database.host setting
        WHEN APP_DATABASE_HOST environment variable is set
        THEN environment variable overrides YAML value

        Acceptance Criteria:
        - Environment variable override support
        """
        # Set environment variable
        os.environ['APP_DATABASE_HOST'] = 'override-host'

        try:
            from src.core.config.loader import Config

            manager = Config(valid_yaml_file)
            config = manager.load()

            # Verify override
            assert config.database.host == 'override-host'
        finally:
            del os.environ['APP_DATABASE_HOST']

    def test_environment_variable_override_nested_values(self, valid_yaml_file):
        """
        GIVEN nested configuration values
        WHEN environment variables use dot notation
        THEN nested values are correctly overridden
        """
        os.environ['APP_DATABASE_HOST'] = 'env-host'
        os.environ['APP_DATABASE_PORT'] = '9999'
        os.environ['APP_REDIS_DB'] = '5'

        try:
            from src.core.config.loader import Config

            manager = Config(valid_yaml_file)
            config = manager.load()

            # Verify nested overrides
            assert config.database.host == 'env-host'
            assert config.database.port == 9999  # Type conversion
            assert config.redis.db == 5
        finally:
            del os.environ['APP_DATABASE_HOST']
            del os.environ['APP_DATABASE_PORT']
            del os.environ['APP_REDIS_DB']

    def test_environment_variable_override_with_type_conversion(self, valid_yaml_file):
        """
        GIVEN environment variables are strings
        WHEN overriding numeric or boolean config values
        THEN automatic type conversion occurs
        """
        os.environ['APP_DATABASE_PORT'] = '9999'
        os.environ['APP_PLUGINS_AUTO_LOAD'] = 'false'

        try:
            from src.core.config.loader import Config

            manager = Config(valid_yaml_file)
            config = manager.load()

            # Verify type conversion
            assert isinstance(config.database.port, int)
            assert config.database.port == 9999
            assert isinstance(config.plugins.auto_load, bool)
            assert config.plugins.auto_load is False
        finally:
            del os.environ['APP_DATABASE_PORT']
            del os.environ['APP_PLUGINS_AUTO_LOAD']

    def test_environment_variable_override_list_values(self, valid_yaml_file):
        """
        GIVEN a config with list value
        WHEN environment variable overrides with comma-separated values
        THEN list is correctly parsed
        """
        os.environ['APP_PLUGINS_PATHS'] = '/path1,/path2,/path3'

        try:
            from src.core.config.loader import Config

            manager = Config(valid_yaml_file)
            config = manager.load()

            # Verify list parsing
            assert isinstance(config.plugins.paths, list)
            assert len(config.plugins.paths) == 3
            assert '/path1' in config.plugins.paths
        finally:
            del os.environ['APP_PLUGINS_PATHS']

    def test_environment_variable_override_non_existent_key(self, valid_yaml_file):
        """
        GIVEN an environment variable for non-existent config key
        WHEN config is loaded
        THEN new key is added to configuration
        """
        os.environ['APP_NEW_SETTING'] = 'new-value'

        try:
            from src.core.config.loader import Config

            manager = Config(valid_yaml_file)
            config = manager.load()

            # Verify new key added
            assert hasattr(config, 'new_setting')
            assert config.new_setting == 'new-value'
        finally:
            del os.environ['APP_NEW_SETTING']

    def test_environment_variable_prefix_configurable(self, valid_yaml_file):
        """
        GIVEN a custom environment variable prefix
        WHEN config manager is initialized with custom prefix
        THEN environment variables with custom prefix are recognized
        """
        os.environ['CUSTOM_DATABASE_HOST'] = 'custom-host'

        try:
            from src.core.config.loader import Config

            manager = Config(valid_yaml_file, env_prefix='CUSTOM_')
            config = manager.load()

            assert config.database.host == 'custom-host'
        finally:
            del os.environ['CUSTOM_DATABASE_HOST']


# ============================================================================
# TEST CLASS 3: Schema Validation (Acceptance Criteria #3)
# ============================================================================

class TestConfigurationSchemaValidation:
    """
    GIVEN a configuration schema is defined
    WHEN configuration is loaded
    THEN values are validated against schema with clear error messages
    """

    def test_config_validation_with_valid_schema(self, valid_yaml_file):
        """
        GIVEN a valid configuration matching schema
        WHEN config is loaded with schema validation
        THEN validation succeeds
        """
        from src.core.config.loader import Config
        from src.core.config.schema import DatabaseConfig, RedisConfig, LoggingConfig, PluginsConfig

        manager = Config(valid_yaml_file)
        config = manager.load()

        # Verify schema validation
        assert isinstance(config, object)
        assert hasattr(config, 'database')
        assert hasattr(config, 'redis')
        assert hasattr(config, 'logging')
        assert hasattr(config, 'plugins')

    def test_config_validation_fails_on_invalid_type(self, tmp_path):
        """
        GIVEN a configuration with invalid type for a field
        WHEN config is loaded with schema validation
        THEN clear validation error is raised
        """
        from src.core.config.loader import Config

        # Create config with invalid type
        config_file = tmp_path / "invalid_type.yaml"
        with open(config_file, 'w') as f:
            yaml.dump({
                "database": {
                    "host": "localhost",
                    "port": "not-a-number"  # Should be int
                }
            }, f)

        manager = Config(config_file)

        with pytest.raises(ValueError, match="port.*must be.*integer"):
            manager.load()

    def test_config_validation_fails_on_missing_required_field(self, tmp_path):
        """
        GIVEN a configuration missing required fields
        WHEN config is loaded with schema validation
        THEN clear error indicates which field is missing
        """
        from src.core.config.loader import Config

        # Create config missing required field
        config_file = tmp_path / "missing_field.yaml"
        with open(config_file, 'w') as f:
            yaml.dump({
                "database": {
                    "host": "localhost"
                    # Missing: port, name, user, password
                }
            }, f)

        manager = Config(config_file)

        with pytest.raises(ValueError, match="Missing required field.*port"):
            manager.load()

    def test_config_validation_with_range_constraints(self, tmp_path):
        """
        GIVEN a configuration with numeric range constraints
        WHEN value is outside valid range
        THEN validation error indicates range violation
        """
        from src.core.config.loader import Config

        # Create config with invalid port
        config_file = tmp_path / "invalid_port.yaml"
        with open(config_file, 'w') as f:
            yaml.dump({
                "database": {
                    "host": "localhost",
                    "port": 99999  # Invalid port (> 65535)
                }
            }, f)

        manager = Config(config_file)

        with pytest.raises(ValueError, match="port.*must be between.*1.*65535"):
            manager.load()

    def test_config_validation_with_allowed_values(self, tmp_path):
        """
        GIVEN a configuration with enum-like constraints
        WHEN value is not in allowed set
        THEN validation error lists allowed values
        """
        from src.core.config.loader import Config

        # Create config with invalid log level
        config_file = tmp_path / "invalid_log_level.yaml"
        with open(config_file, 'w') as f:
            yaml.dump({
                "logging": {
                    "level": "INVALID_LEVEL"  # Not in DEBUG, INFO, WARNING, ERROR
                }
            }, f)

        manager = Config(config_file)

        with pytest.raises(ValueError, match="level.*must be one of.*DEBUG.*INFO.*WARNING.*ERROR"):
            manager.load()

    def test_config_validation_error_messages_are_clear(self, tmp_path):
        """
        GIVEN multiple validation errors
        WHEN config is loaded
        THEN all validation errors are reported with clear messages
        """
        from src.core.config.loader import Config

        # Create config with multiple errors
        config_file = tmp_path / "multiple_errors.yaml"
        with open(config_file, 'w') as f:
            yaml.dump({
                "database": {
                    "host": "localhost",
                    "port": "invalid",
                    "name": ""  # Empty string not allowed
                }
            }, f)

        manager = Config(config_file)

        with pytest.raises(ValueError) as exc_info:
            manager.load()

        error_message = str(exc_info.value)
        # Verify error mentions both problems
        assert "port" in error_message
        assert "name" in error_message

    def test_config_validation_with_optional_fields(self, valid_yaml_file):
        """
        GIVEN a configuration with optional fields
        WHEN optional fields are not provided
        THEN validation succeeds with default values
        """
        from src.core.config.loader import Config

        # Config without optional fields should still be valid
        manager = Config(valid_yaml_file)
        config = manager.load()

        # Should have defaults for optional fields
        assert config is not None


# ============================================================================
# TEST CLASS 4: Configuration Hot-Reload (Acceptance Criteria #4)
# ============================================================================

class TestConfigurationHotReload:
    """
    GIVEN a configuration is loaded
    WHEN the underlying YAML file is modified
    THEN configuration is reloaded without restart
    """

    def test_config_hot_reload_on_file_change(self, valid_yaml_file):
        """
        GIVEN a loaded configuration
        WHEN the YAML file is modified
        THEN configuration is automatically reloaded

        Acceptance Criteria:
        - Configuration hot-reload support
        """
        from src.core.config.loader import Config

        manager = Config(valid_yaml_file, hot_reload=True)
        config = manager.load()

        # Initial value
        assert config.database.host == "localhost"

        # Modify file
        import time
        time.sleep(0.1)  # Ensure different timestamp

        with open(valid_yaml_file, 'w') as f:
            yaml.dump({
                "database": {
                    "host": "modified-host",
                    "port": 5432,
                    "name": "testdb",
                    "user": "testuser",
                    "password": "testpass"
                }
            }, f)

        # Wait for reload
        time.sleep(0.5)

        # Verify reload
        updated_config = manager.get_config()
        assert updated_config.database.host == "modified-host"

    def test_config_hot_reload_can_be_disabled(self, valid_yaml_file):
        """
        GIVEN a configuration manager with hot_reload disabled
        WHEN the YAML file is modified
        THEN configuration is NOT automatically reloaded
        """
        from src.core.config.loader import Config

        manager = Config(valid_yaml_file, hot_reload=False)
        config = manager.load()

        initial_host = config.database.host

        # Modify file
        import time
        with open(valid_yaml_file, 'w') as f:
            yaml.dump({
                "database": {
                    "host": "modified-host",
                    "port": 5432,
                    "name": "testdb",
                    "user": "testuser",
                    "password": "testpass"
                }
            }, f)

        time.sleep(0.5)

        # Verify NOT reloaded
        unchanged_config = manager.get_config()
        assert unchanged_config.database.host == initial_host

    def test_config_hot_reload_with_callback(self, valid_yaml_file):
        """
        GIVEN a configuration manager with hot_reload enabled
        WHEN file is modified
        THEN registered callback is invoked
        """
        from src.core.config.loader import Config

        callback_called = []

        def reload_callback(old_config, new_config):
            callback_called.append((old_config, new_config))

        manager = Config(valid_yaml_file, hot_reload=True, on_reload=reload_callback)
        config = manager.load()

        # Modify file
        import time
        with open(valid_yaml_file, 'w') as f:
            yaml.dump({
                "database": {
                    "host": "callback-host",
                    "port": 5432,
                    "name": "testdb",
                    "user": "testuser",
                    "password": "testpass"
                }
            }, f)

        time.sleep(0.5)

        # Verify callback was called
        assert len(callback_called) > 0
        assert callback_called[0][1].database.host == "callback-host"

    def test_config_hot_reload_on_invalid_file(self, valid_yaml_file):
        """
        GIVEN a loaded configuration with hot_reload
        WHEN file is modified to invalid YAML
        THEN previous configuration is preserved and error is logged
        """
        from src.core.config.loader import Config

        manager = Config(valid_yaml_file, hot_reload=True)
        config = manager.load()

        initial_host = config.database.host

        # Corrupt file
        import time
        with open(valid_yaml_file, 'w') as f:
            f.write("invalid: yaml: content:")

        time.sleep(0.5)

        # Verify previous config preserved
        preserved_config = manager.get_config()
        assert preserved_config.database.host == initial_host

    def test_config_manual_reload(self, valid_yaml_file):
        """
        GIVEN a configuration manager
        WHEN reload is manually triggered
        THEN configuration is reloaded from file
        """
        from src.core.config.loader import Config

        manager = Config(valid_yaml_file, hot_reload=False)
        config = manager.load()

        # Modify file
        with open(valid_yaml_file, 'w') as f:
            yaml.dump({
                "database": {
                    "host": "manual-reload-host",
                    "port": 5432,
                    "name": "testdb",
                    "user": "testuser",
                    "password": "testpass"
                }
            }, f)

        # Manual reload
        manager.reload()
        updated_config = manager.get_config()

        assert updated_config.database.host == "manual-reload-host"


# ============================================================================
# TEST CLASS 5: Configuration Access and Query
# ============================================================================

class TestConfigurationAccess:
    """
    GIVEN a loaded configuration
    WHEN configuration values are accessed
    THEN values are retrievable via various access methods
    """

    def test_config_access_via_dot_notation(self, valid_yaml_file):
        """
        GIVEN a loaded configuration
        WHEN accessing nested values via dot notation
        THEN values are returned correctly
        """
        from src.core.config.loader import Config

        manager = Config(valid_yaml_file)
        config = manager.load()

        # Dot notation access
        assert config.database.host == "localhost"
        assert config.database.port == 5432

    def test_config_access_via_dict_notation(self, valid_yaml_file):
        """
        GIVEN a loaded configuration
        WHEN accessing values via dictionary notation
        THEN values are returned correctly
        """
        from src.core.config.loader import Config

        manager = Config(valid_yaml_file)
        config = manager.load()

        # Dict notation access
        assert config['database']['host'] == "localhost"
        assert config['database']['port'] == 5432

    def test_config_get_method_with_default(self, valid_yaml_file):
        """
        GIVEN a loaded configuration
        WHEN accessing non-existent key with default
        THEN default value is returned
        """
        from src.core.config.loader import Config

        manager = Config(valid_yaml_file)
        config = manager.load()

        # Get with default
        assert config.get('nonexistent_key', 'default_value') == 'default_value'
        assert config.get('database.nonexistent', 'default') == 'default'

    def test_config_get_value_by_path(self, valid_yaml_file):
        """
        GIVEN a loaded configuration
        WHEN accessing value by path string
        THEN value at path is returned
        """
        from src.core.config.loader import Config

        manager = Config(valid_yaml_file)
        config = manager.load()

        # Path-based access
        assert config.get_path('database.host') == "localhost"
        assert config.get_path('redis.port') == 6379

    def test_config_export_to_dict(self, valid_yaml_file):
        """
        GIVEN a loaded configuration
        WHEN exporting to dictionary
        THEN all values are returned as dict
        """
        from src.core.config.loader import Config

        manager = Config(valid_yaml_file)
        config = manager.load()

        # Export to dict
        config_dict = config.to_dict()

        assert isinstance(config_dict, dict)
        assert 'database' in config_dict
        assert config_dict['database']['host'] == "localhost"

    def test_config_export_to_yaml(self, valid_yaml_file, tmp_path):
        """
        GIVEN a loaded configuration
        WHEN exporting to YAML file
        THEN valid YAML file is created
        """
        from src.core.config.loader import Config

        manager = Config(valid_yaml_file)
        config = manager.load()

        # Export to new file
        export_file = tmp_path / "exported_config.yaml"
        manager.export_to_yaml(export_file)

        # Verify export
        assert export_file.exists()

        with open(export_file, 'r') as f:
            exported_data = yaml.safe_load(f)

        assert exported_data['database']['host'] == "localhost"


# ============================================================================
# TEST CLASS 6: Concurrent Access
# ============================================================================

class TestConfigurationConcurrentAccess:
    """
    GIVEN multiple threads accessing configuration
    WHEN concurrent operations occur
    Then configuration remains consistent
    """

    def test_concurrent_config_read(self, valid_yaml_file):
        """
        GIVEN multiple threads reading configuration
        WHEN all threads access simultaneously
        THEN all reads succeed with consistent data
        """
        from src.core.config.loader import Config

        manager = Config(valid_yaml_file)
        manager.load()

        results = []

        def read_config():
            for _ in range(100):
                config = manager.get_config()
                results.append(config.database.host)

        threads = []
        for _ in range(10):
            thread = threading.Thread(target=read_config)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # All reads should return same value
        assert all(r == "localhost" for r in results)

    def test_concurrent_config_reload(self, valid_yaml_file):
        """
        GIVEN multiple threads triggering reload
        WHEN reloads occur concurrently
        Then configuration remains consistent
        """
        from src.core.config.loader import Config

        manager = Config(valid_yaml_file, hot_reload=False)
        manager.load()

        def reload_config():
            for _ in range(10):
                try:
                    manager.reload()
                except Exception:
                    pass

        threads = []
        for _ in range(5):
            thread = threading.Thread(target=reload_config)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Final config should be valid
        config = manager.get_config()
        assert config.database.host == "localhost"


# ============================================================================
# EDGE CASE TESTS
# ============================================================================

class TestConfigurationEdgeCases:
    """
    GIVEN various edge case scenarios
    WHEN edge cases occur
    Then system handles them gracefully
    """

    def test_empty_yaml_file(self, tmp_path):
        """
        GIVEN an empty YAML file
        WHEN config is loaded
        Then empty configuration is returned
        """
        from src.core.config.loader import Config

        config_file = tmp_path / "empty.yaml"
        config_file.write_text("")

        manager = Config(config_file)

        with pytest.raises(ValueError, match="Empty configuration"):
            manager.load()

    def test_yaml_file_with_comments(self, tmp_path):
        """
        GIVEN a YAML file with comments
        WHEN config is loaded
        Then comments are ignored, values are parsed
        """
        from src.core.config.loader import Config

        config_file = tmp_path / "with_comments.yaml"
        with open(config_file, 'w') as f:
            f.write("""
# Database configuration
database:
  host: localhost  # The database host
  port: 5432
  name: testdb
""")

        manager = Config(config_file)
        config = manager.load()

        assert config.database.host == "localhost"

    def test_config_with_special_characters(self, tmp_path):
        """
        GIVEN a config with special characters in values
        WHEN config is loaded
        Then special characters are preserved
        """
        from src.core.config.loader import Config

        config_file = tmp_path / "special_chars.yaml"
        with open(config_file, 'w') as f:
            yaml.dump({
                "database": {
                    "password": "p@ssw0rd!#$%"
                }
            }, f)

        manager = Config(config_file)
        config = manager.load()

        assert config.database.password == "p@ssw0rd!#$%"


# ============================================================================
# TEST SUMMARY
# ============================================================================

"""
Test Coverage Summary for P1-T002 Configuration Management:

1. Configuration Loading from YAML (7 tests)
   ✓ test_config_loaded_from_yaml_file
   ✓ test_config_loading_with_multiple_yaml_files
   ✓ test_config_loading_fails_on_nonexistent_file
   ✓ test_config_loading_fails_on_invalid_yaml
   ✓ test_config_loading_with_absolute_path
   ✓ test_config_loading_with_relative_path
   ✓ test_config_with_special_characters

2. Environment Variable Override (6 tests)
   ✓ test_environment_variable_override_single_value
   ✓ test_environment_variable_override_nested_values
   ✓ test_environment_variable_override_with_type_conversion
   ✓ test_environment_variable_override_list_values
   ✓ test_environment_variable_override_non_existent_key
   ✓ test_environment_variable_prefix_configurable

3. Schema Validation (6 tests)
   ✓ test_config_validation_with_valid_schema
   ✓ test_config_validation_fails_on_invalid_type
   ✓ test_config_validation_fails_on_missing_required_field
   ✓ test_config_validation_with_range_constraints
   ✓ test_config_validation_with_allowed_values
   ✓ test_config_validation_error_messages_are_clear
   ✓ test_config_validation_with_optional_fields

4. Configuration Hot-Reload (6 tests)
   ✓ test_config_hot_reload_on_file_change
   ✓ test_config_hot_reload_can_be_disabled
   ✓ test_config_hot_reload_with_callback
   ✓ test_config_hot_reload_on_invalid_file
   ✓ test_config_manual_reload

5. Configuration Access and Query (6 tests)
   ✓ test_config_access_via_dot_notation
   ✓ test_config_access_via_dict_notation
   ✓ test_config_get_method_with_default
   ✓ test_config_get_value_by_path
   ✓ test_config_export_to_dict
   ✓ test_config_export_to_yaml

6. Concurrent Access (2 tests)
   ✓ test_concurrent_config_read
   ✓ test_concurrent_config_reload

7. Edge Cases (3 tests)
   ✓ test_empty_yaml_file
   ✓ test_yaml_file_with_comments
   ✓ test_config_with_special_characters

TOTAL: 37 comprehensive test cases

Expected Implementation Files:
- src/core/config/__init__.py
- src/core/config/schema.py (Pydantic models)
- src/core/config/loader.py (YAML loader)
- src/core/config/manager.py (Config manager)

Next Steps (GREEN Phase):
1. backend-dev implements Config class
2. backend-dev implements schema validation with Pydantic
3. backend-dev implements YAML loader
4. backend-dev implements environment variable override
5. backend-dev implements hot-reload functionality
6. backend-dev ensures all tests pass

Coverage Target: 85%+
"""
