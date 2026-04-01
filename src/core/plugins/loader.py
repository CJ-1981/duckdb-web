"""
Plugin Loader

Dynamically loads plugins from configured filesystem paths.
Handles plugin discovery, metadata parsing, and plugin instantiation.
"""

import json
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from importlib.util import spec_from_file_location, module_from_spec
import sys

from .base import Plugin, PluginMetadata

logger = logging.getLogger(__name__)


class PluginLoader:
    """
    Dynamic plugin loader from filesystem paths

    Discovers plugins in directories and loads them with metadata.
    """

    def __init__(self, search_paths: List[Path]):
        """
        Initialize plugin loader with search paths

        Args:
            search_paths: List of directories to search for plugins
        """
        self.search_paths = [Path(p) for p in search_paths]
        self._loaded_plugins: Dict[str, Plugin] = {}

    def discover_plugins(self) -> Dict[str, Path]:
        """
        Discover all plugin directories in search paths

        Returns:
            Dictionary mapping plugin names to their directory paths
        """
        discovered = {}

        for search_path in self.search_paths:
            if not search_path.exists():
                logger.warning(f"Plugin search path does not exist: {search_path}")
                continue

            if not search_path.is_dir():
                logger.warning(f"Plugin search path is not a directory: {search_path}")
                continue

            # Find all subdirectories with plugin.json
            for plugin_dir in search_path.iterdir():
                if plugin_dir.is_dir():
                    metadata_file = plugin_dir / "plugin.json"
                    if metadata_file.exists():
                        try:
                            metadata = self._load_metadata(metadata_file)
                            plugin_name = metadata["name"]
                            discovered[plugin_name] = plugin_dir
                        except Exception as e:
                            logger.warning(f"Failed to load metadata from {metadata_file}: {e}")

        return discovered

    def _load_metadata(self, metadata_file: Path) -> Dict[str, Any]:
        """
        Load plugin metadata from JSON file

        Args:
            metadata_file: Path to plugin.json file

        Returns:
            Dictionary containing plugin metadata

        Raises:
            ValueError: If metadata file is invalid
        """
        try:
            with open(metadata_file, 'r') as f:
                data = json.load(f)

            # Validate required fields
            required_fields = ["name", "version"]
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"Missing required field: {field}")

            return data
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in metadata file: {e}")

    def load_plugin_from_directory(self, plugin_dir: Path) -> Optional[Plugin]:
        """
        Load a single plugin from directory

        Args:
            plugin_dir: Directory containing plugin

        Returns:
            Plugin instance or None if loading failed
        """
        metadata_file = plugin_dir / "plugin.json"

        if not metadata_file.exists():
            logger.warning(f"No plugin.json found in {plugin_dir}")
            return None

        try:
            # Load metadata
            metadata_dict = self._load_metadata(metadata_file)
            metadata = PluginMetadata(
                name=metadata_dict["name"],
                version=metadata_dict["version"],
                description=metadata_dict.get("description", ""),
                author=metadata_dict.get("author", ""),
                dependencies=metadata_dict.get("dependencies", []),
                lifecycle_hooks=metadata_dict.get("lifecycle_hooks", []),
            )

            # Look for plugin.py file
            plugin_file = plugin_dir / "plugin.py"
            if plugin_file.exists():
                return self._load_plugin_class(plugin_file, metadata)
            else:
                # Create a basic plugin wrapper if no plugin.py
                return self._create_basic_plugin(metadata)

        except Exception as e:
            logger.error(f"Failed to load plugin from {plugin_dir}: {e}")
            return None

    def _load_plugin_class(self, plugin_file: Path, metadata: PluginMetadata) -> Optional[Plugin]:
        """
        Load plugin class from Python file

        Args:
            plugin_file: Path to plugin.py file
            metadata: Plugin metadata

        Returns:
            Plugin instance or None if loading failed
        """
        try:
            # Create module spec
            module_name = f"plugin_{metadata.name}"
            spec = spec_from_file_location(module_name, plugin_file)

            if spec is None or spec.loader is None:
                logger.error(f"Failed to create module spec for {plugin_file}")
                return None

            # Load module
            module = module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

            # Find Plugin class in module
            if hasattr(module, 'Plugin'):
                plugin_class = getattr(module, 'Plugin')
                return plugin_class(metadata)
            else:
                logger.warning(f"No Plugin class found in {plugin_file}")
                return None

        except Exception as e:
            logger.error(f"Failed to load plugin class from {plugin_file}: {e}")
            return None

    def _create_basic_plugin(self, metadata: PluginMetadata) -> Plugin:
        """
        Create a basic plugin implementation

        Args:
            metadata: Plugin metadata

        Returns:
            Basic plugin instance
        """
        from .base import Plugin as BasePlugin

        class BasicPlugin(BasePlugin):
            """Basic plugin implementation with default lifecycle hooks"""

            def on_load(self) -> bool:
                return True

            def on_enable(self) -> bool:
                return True

            def on_disable(self) -> bool:
                return True

            def on_unload(self) -> bool:
                return True

        return BasicPlugin(metadata)

    def load_all_plugins(self) -> Dict[str, Plugin]:
        """
        Load all plugins from search paths

        Returns:
            Dictionary mapping plugin names to plugin instances
        """
        discovered = self.discover_plugins()
        loaded = {}

        for plugin_name, plugin_dir in discovered.items():
            plugin = self.load_plugin_from_directory(plugin_dir)
            if plugin is not None:
                loaded[plugin_name] = plugin
                logger.info(f"Loaded plugin: {plugin_name} v{plugin.version}")
            else:
                logger.warning(f"Failed to load plugin: {plugin_name}")

        return loaded
