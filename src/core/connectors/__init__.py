"""
Data Connectors Module

Provides connectors for various data sources to import data into DuckDB.
"""

from .base import BaseConnector
from .csv import CSVConnector
from .api import APIConnector, create_api_connector

__all__ = [
    'BaseConnector',
    'CSVConnector',
    'APIConnector',
    'create_api_connector',
]


# Connector registry
CONNECTOR_REGISTRY = {
    'csv': CSVConnector,
    'api': APIConnector,
}


def get_connector(connector_type: str) -> type:
    """
    Get connector class by type

    Args:
        connector_type: Type identifier (e.g., 'csv')

    Returns:
        Connector class

    Raises:
        KeyError: If connector type not found
    """
    if connector_type not in CONNECTOR_REGISTRY:
        raise KeyError(f"Unknown connector type: {connector_type}. "
                      f"Available types: {list(CONNECTOR_REGISTRY.keys())}")

    return CONNECTOR_REGISTRY[connector_type]


def register_connector(connector_type: str, connector_class: type) -> None:
    """
    Register a new connector type

    Args:
        connector_type: Type identifier
        connector_class: Connector class (must inherit from BaseConnector)
    """
    if not issubclass(connector_class, BaseConnector):
        raise TypeError(f"{connector_class} must inherit from BaseConnector")

    CONNECTOR_REGISTRY[connector_type] = connector_class
