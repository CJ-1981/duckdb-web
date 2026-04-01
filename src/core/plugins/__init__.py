"""
Plugin System for Data Analysis Platform

This module provides a dynamic plugin loading and lifecycle management system.
Supports concurrent access, dependency resolution, and plugin metadata inspection.

Components:
- Plugin: Base plugin class with lifecycle hooks
- PluginMetadata: Plugin metadata structure
- PluginLoader: Dynamic plugin loading from paths
- PluginRegistry: Central registry with concurrent access
- PluginLifecycle: Lifecycle hook execution manager
"""

from .base import Plugin, PluginMetadata, PluginStatus
from .registry import PluginRegistry, DependencyError

__all__ = [
    "Plugin",
    "PluginMetadata",
    "PluginStatus",
    "PluginRegistry",
    "DependencyError",
]
