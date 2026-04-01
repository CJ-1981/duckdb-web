"""
Base Connector Interface

Defines the abstract interface for all data connectors.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Iterator, Optional
from pathlib import Path


class BaseConnector(ABC):
    """
    Abstract base class for data connectors

    All connectors must implement these methods for data ingestion
    into the DuckDB data processing platform.
    """

    def __init__(self):
        """Initialize connector with default configuration"""
        pass

    @abstractmethod
    def connect(self, **kwargs) -> None:
        """
        Establish connection to data source

        Args:
            **kwargs: Connection parameters
        """
        pass

    @abstractmethod
    def read(self, **kwargs) -> Iterator[Dict[str, Any]]:
        """
        Read data from source

        Yields:
            Dictionary representing a single row/record
        """
        pass

    @abstractmethod
    def validate(self, **kwargs) -> bool:
        """
        Validate data source configuration

        Returns:
            True if valid, raises exception otherwise
        """
        pass

    @abstractmethod
    def get_metadata(self, **kwargs) -> Dict[str, Any]:
        """
        Get metadata about data source

        Returns:
            Dictionary with metadata (row count, columns, etc.)
        """
        pass
