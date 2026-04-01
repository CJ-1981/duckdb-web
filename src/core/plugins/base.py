"""
Base Plugin Classes

Defines the core plugin abstractions and lifecycle hooks.
All plugins must inherit from Plugin and implement lifecycle methods.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass, field


class PluginStatus(Enum):
    """Plugin lifecycle status states"""
    LOADED = "loaded"
    ENABLED = "enabled"
    DISABLED = "disabled"
    UNLOADED = "unloaded"


@dataclass
class PluginMetadata:
    """
    Plugin metadata structure

    Attributes:
        name: Unique plugin identifier
        version: Semantic version string
        description: Human-readable description
        author: Plugin author name
        dependencies: List of required plugin dependencies
        lifecycle_hooks: List of supported lifecycle hooks
    """
    name: str
    version: str
    description: str = ""
    author: str = ""
    dependencies: list[str] = field(default_factory=list)
    lifecycle_hooks: list[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary"""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "dependencies": self.dependencies,
            "lifecycle_hooks": self.lifecycle_hooks,
        }


class Plugin(ABC):
    """
    Abstract base class for all plugins

    All plugins must implement lifecycle hooks:
    - on_load(): Called when plugin is first loaded
    - on_enable(): Called when plugin is enabled
    - on_disable(): Called when plugin is disabled
    - on_unload(): Called when plugin is unloaded

    Lifecycle Order:
    on_load -> on_enable -> on_disable -> on_unload
    """

    def __init__(self, metadata: PluginMetadata):
        """
        Initialize plugin with metadata

        Args:
            metadata: Plugin metadata instance
        """
        self.metadata = metadata
        self.name = metadata.name
        self.version = metadata.version
        self._status = PluginStatus.LOADED

    @property
    def status(self) -> PluginStatus:
        """Get current plugin status"""
        return self._status

    def _set_status(self, status: PluginStatus) -> None:
        """Set plugin status (internal use)"""
        self._status = status

    @abstractmethod
    def on_load(self) -> bool:
        """
        Called when plugin is loaded into registry

        Returns:
            True if load successful, False otherwise
        """
        pass

    @abstractmethod
    def on_enable(self) -> bool:
        """
        Called when plugin is enabled

        Returns:
            True if enable successful, False otherwise
        """
        pass

    @abstractmethod
    def on_disable(self) -> bool:
        """
        Called when plugin is disabled

        Returns:
            True if disable successful, False otherwise
        """
        pass

    @abstractmethod
    def on_unload(self) -> bool:
        """
        Called when plugin is unloaded from registry

        Returns:
            True if unload successful, False otherwise
        """
        pass

    def __repr__(self) -> str:
        return f"Plugin(name={self.name}, version={self.version}, status={self._status.value})"
