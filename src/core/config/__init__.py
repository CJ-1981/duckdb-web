"""
Configuration Management Module

Provides Pydantic-based configuration management with YAML support,
environment variable overrides, and hot-reload capability.
"""

from .schema import ConfigSchema
from .loader import Config

__all__ = ['Config', 'ConfigSchema', 'load_config']
