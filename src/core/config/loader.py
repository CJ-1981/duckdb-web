"""
Configuration Loader with Hot-Reload Support

Implements thread-safe configuration management with YAML loading,
environment variable overrides, and automatic file watching for hot-reload.
"""

import os
import threading
import time
import yaml
from pathlib import Path
from typing import Any, Dict, Optional, Callable, List, Union
from pydantic import ValidationError

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    Observer = None
    FileSystemEventHandler = None
    WATCHDOG_AVAILABLE = False

from .schema import ConfigSchema


class ConfigReloadHandler:
    """File system event handler for configuration hot-reload"""

    def __init__(self, callback: Callable[[], None], config_file: Path):
        if FileSystemEventHandler is not None:
            super().__init__()
        else:
            # Fallback without FileSystemEventHandler
            pass
        self.callback = callback
        self.config_file = config_file
        self._last_modified = 0

    def on_modified(self, event):
        """Handle file modification events"""
        if FileSystemEventHandler is None:
            return  # Hot-reload not available
        if event.src_path == str(self.config_file):
            # Prevent multiple rapid reloads
            current_time = time.time()
            if current_time - self._last_modified > 0.5:  # 500ms debounce
                self._last_modified = current_time
                try:
                    self.callback()
                except Exception as e:
                    # Log error but don't crash the watcher
                    print(f"Error reloading config: {e}")


class Config:
    """
    Thread-safe configuration manager with hot-reload support

    Features:
    - Load from YAML files with validation
    - Environment variable overrides (nested dot notation)
    - Thread-safe concurrent access
    - Hot-reload on file changes
    - Dictionary and dot notation access
    """

    _instance = None
    _lock = threading.RLock()
    _watcher_thread = None
    _watcher_running = False

    def __init__(self, config_path: Union[str, Path, List[Union[str, Path]]], env_prefix: str = "APP", hot_reload: bool = True):
        """
        Initialize configuration manager

        Args:
            config_path: Path to YAML configuration file, or list of paths (merged in order)
            env_prefix: Prefix for environment variable overrides (underscore will be added if not present)
            hot_reload: Enable hot-reload on file changes
        """
        if isinstance(config_path, list):
            self._config_paths = [Path(p) for p in config_path]
            self._config_path = self._config_paths[0]  # Primary path for hot-reload
        else:
            self._config_path = Path(config_path)
            self._config_paths = [self._config_path]
        # Normalize env_prefix to ensure it ends with underscore
        self._env_prefix = env_prefix if env_prefix.endswith('_') else f'{env_prefix}_'
        self._schema: Optional[ConfigSchema] = None
        self._raw_data: Dict[str, Any] = {}
        self._observers: List[Callable[[], None]] = []
        self._hot_reload_enabled = hot_reload
        self._observer: Optional[Observer] = None
        self._watcher_thread: Optional[threading.Thread] = None

    @classmethod
    def get_instance(cls) -> 'Config':
        """Get singleton instance (not used in this implementation)"""
        raise NotImplementedError("Use direct instantiation instead")

    def load(self) -> 'Config':
        """
        Load configuration from YAML file(s)

        Returns:
            Config: Self for chained access

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config file is empty
            yaml.YAMLError: If YAML is invalid
            ValidationError: If config validation fails
        """
        with self._lock:
            # Check all files exist
            for config_path in self._config_paths:
                if not config_path.exists():
                    raise FileNotFoundError(f"Configuration file not found: {config_path}")

            # Load and merge YAML files (later files override earlier ones)
            self._raw_data = {}
            for config_path in self._config_paths:
                try:
                    with open(config_path, 'r') as f:
                        data = yaml.safe_load(f)
                        if data is None:
                            raise ValueError(f"Empty configuration file: {config_path}")
                        # Deep merge
                        self._deep_merge(self._raw_data, data)
                except yaml.YAMLError as e:
                    raise yaml.YAMLError(f"Invalid YAML in {config_path}: {e}")

            # Apply environment variable overrides
            self._apply_env_overrides()

            # Validate and create schema
            self._schema = ConfigSchema.model_validate(self._raw_data)

            return self

    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> None:
        """
        Deep merge override dict into base dict

        Args:
            base: Base dictionary to merge into
            override: Override dictionary with values to merge
        """
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value

    def _apply_env_overrides(self):
        """
        Apply environment variable overrides to configuration

        Environment variable naming convention:
        - Single underscore for section separation: APP_DATABASE_HOST -> database.host
        - Double underscore for explicit nesting: APP_DATABASE__HOST -> database.host (same as single)
        - Field names with underscores are preserved: APP_PLUGINS_AUTO_LOAD -> plugins.auto_load

        The method intelligently handles field names with underscores by checking against known sections.
        """
        for key, value in os.environ.items():
            if key.startswith(self._env_prefix):
                # Remove prefix (already includes underscore)
                config_key = key[len(self._env_prefix):].lower()

                # Split into parts by underscore
                parts = config_key.split('_')

                # Try to find the best split point for section.field
                # Known top-level sections
                known_sections = {'database', 'redis', 'logging', 'plugins'}

                if parts and parts[0] in known_sections:
                    section = parts[0]
                    remaining = '_'.join(parts[1:])  # Preserve underscores in field name
                    config_key = f'{section}.{remaining}'
                else:
                    # Fallback: convert all underscores to dots
                    config_key = config_key.replace('_', '.')

                # Support dot notation for nested keys
                keys = config_key.split('.')
                self._set_nested_value(self._raw_data, keys, self._convert_env_value(value))

    def _set_nested_value(self, data: Dict[str, Any], keys: List[str], value: Any):
        """
        Set nested dictionary value using key path

        Args:
            data: Dictionary to update
            keys: List of keys representing nested path
            value: Value to set
        """
        current = data
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
            if not isinstance(current, dict):
                # Path exists but isn't a dict, can't nest further
                return
        current[keys[-1]] = value

    def _convert_env_value(self, value: str) -> Any:
        """
        Convert environment variable string to appropriate type

        Attempts to parse as int, float, bool, list, or dict

        Args:
            value: String value from environment

        Returns:
            Converted value (int, float, bool, list, dict, or str)
        """
        # Try boolean
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'

        # Try integer
        try:
            return int(value)
        except ValueError:
            pass

        # Try float
        try:
            return float(value)
        except ValueError:
            pass

        # Try list (comma-separated)
        if ',' in value:
            return [item.strip() for item in value.split(',')]

        # Try dict (JSON-like)
        if value.startswith('{') and value.endswith('}'):
            import json
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                pass

        # Default to string
        return value

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by dot notation

        Args:
            key: Dot-separated key path (e.g., 'database.host')
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        with self._lock:
            if self._schema is None:
                self.load()

            keys = key.split('.')
            value = self._schema
            for k in keys:
                if hasattr(value, k):
                    value = getattr(value, k)
                else:
                    return default
            return value

    def get_config(self) -> 'Config':
        """
        Get the current configuration object

        Returns:
            Config: Self for accessing configuration
        """
        with self._lock:
            if self._schema is None:
                self.load()
            return self

    def get_path(self, path: str, default: Any = None) -> Any:
        """
        Get configuration value by dot notation path (alias for get)

        Args:
            path: Dot-separated key path (e.g., 'database.host')
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        return self.get(path, default)

    def __getitem__(self, key: str) -> Any:
        """
        Dictionary-style access

        Returns dictionaries for nested Pydantic models to support
        chained dictionary access like config['database']['host']
        """
        with self._lock:
            if self._schema is None:
                self.load()

            if hasattr(self._schema, key):
                value = getattr(self._schema, key)
                # Convert Pydantic models to dict for nested access
                if hasattr(value, 'model_dump'):
                    return value.model_dump()
                return value
            raise KeyError(key)

    def __contains__(self, key: str) -> bool:
        """Support 'in' operator for top-level keys"""
        with self._lock:
            if self._schema is None:
                self.load()
            return hasattr(self._schema, key)

    def __getattr__(self, name: str) -> Any:
        """
        Proxy attribute access to schema for direct field access

        Allows config.database.host style access
        """
        # Only proxy if schema is loaded
        if '_schema' in self.__dict__ and self.__dict__['_schema'] is not None:
            schema = self.__dict__['_schema']
            if hasattr(schema, name):
                return getattr(schema, name)
        # Raise AttributeError if not found
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    def to_dict(self) -> Dict[str, Any]:
        """
        Export configuration to dictionary

        Returns:
            Dictionary representation of configuration
        """
        with self._lock:
            if self._schema is None:
                self.load()
            # Use mode='json' to serialize enums as values
            return self._schema.model_dump(mode='json')

    def export_to_yaml(self, path: Optional[Union[str, Path]] = None) -> str:
        """
        Export configuration to YAML format

        Args:
            path: Optional path to save YAML file

        Returns:
            YAML string representation
        """
        with self._lock:
            if self._schema is None:
                self.load()

            yaml_str = yaml.dump(
                self.to_dict(),
                default_flow_style=False,
                sort_keys=False
            )

            if path:
                save_path = Path(path)
                save_path.write_text(yaml_str)

            return yaml_str

    def add_observer(self, callback: Callable[[], None]):
        """
        Add observer for configuration changes

        Args:
            callback: Function to call when config is reloaded
        """
        with self._lock:
            self._observers.append(callback)

    def remove_observer(self, callback: Callable[[], None]):
        """
        Remove observer

        Args:
            callback: Observer function to remove
        """
        with self._lock:
            if callback in self._observers:
                self._observers.remove(callback)

    def _notify_observers(self):
        """Notify all observers of configuration change"""
        for observer in self._observers:
            try:
                observer()
            except Exception as e:
                print(f"Observer error: {e}")

    def reload(self):
        """
        Manually trigger configuration reload

        This method is thread-safe and will notify all observers
        """
        with self._lock:
            try:
                old_schema = self._schema
                self.load()
                self._notify_observers()
            except Exception as e:
                # Preserve previous configuration on error
                self._schema = old_schema
                raise

    def start_hot_reload(self, interval: float = 1.0):
        """
        Start automatic hot-reload on file changes

        Args:
            interval: Polling interval in seconds (fallback if watchdog fails)
        """
        with self._lock:
            if self._watcher_running:
                return  # Already running

            self._watcher_running = True

            def reload_callback():
                """Callback for hot-reload"""
                try:
                    self.reload()
                except Exception as e:
                    print(f"Hot-reload error: {e}")

            event_handler = ConfigReloadHandler(reload_callback, self._config_path)

            if WATCHDOG_AVAILABLE:
                self._observer = Observer()
                self._observer.schedule(event_handler, path=str(self._config_path.parent))
                self._observer.start()

                # Start watcher thread
                self._watcher_thread = threading.Thread(target=self._observer.join, daemon=True)
                self._watcher_thread.start()
            else:
                # Fallback: warn user that hot-reload requires watchdog
                print("Warning: watchdog package not installed. Hot-reload feature disabled.")

    def stop_hot_reload(self):
        """Stop automatic hot-reload"""
        with self._lock:
            if self._observer and WATCHDOG_AVAILABLE:
                self._observer.stop()
                self._observer = None
            self._watcher_running = False

    @property
    def hot_reload_enabled(self) -> bool:
        """Check if hot-reload is enabled"""
        return self._hot_reload_enabled

    @hot_reload_enabled.setter
    def hot_reload_enabled(self, value: bool):
        """Enable or disable hot-reload"""
        self._hot_reload_enabled = value
        if value and not self._watcher_running:
            self.start_hot_reload()
        elif not value and self._watcher_running:
            self.stop_hot_reload()


def load_config(config_path: Union[str, Path], env_prefix: str = "APP") -> Config:
    """
    Convenience function to load configuration

    Args:
        config_path: Path to YAML configuration file
        env_prefix: Prefix for environment variable overrides

    Returns:
        Config: Configuration manager instance
    """
    config = Config(config_path, env_prefix)
    config.load()
    return config
