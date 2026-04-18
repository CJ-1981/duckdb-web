"""
JSON Connector

Provides JSON and JSONL file connector implementation.
"""

import json
import logging
from typing import Iterator, Dict, Any, List, Optional
from pathlib import Path

from .base import BaseConnector

logger = logging.getLogger(__name__)


class JSONConnector(BaseConnector):
    """
    JSON/JSONL file connector.

    Features:
    - JSON file loading (single object or array)
    - JSONL (JSON Lines) file loading
    - Automatic type inference from JSON values
    - Nested structure handling (flattens to columns)
    - Encoding detection (UTF-8 default)

    Example:
        >>> connector = JSONConnector()
        >>> rows = list(connector.read_json('data.json'))
        >>> # or for JSONL
        >>> rows = list(connector.read_jsonl('data.jsonl'))
    """

    # Class constants
    DEFAULT_ENCODING = 'utf-8'

    def __init__(self, encoding: str = DEFAULT_ENCODING):
        """
        Initialize JSON connector.

        Args:
            encoding: File encoding (default: utf-8)
        """
        super().__init__()
        self.encoding = encoding

    def connect(self, **kwargs) -> None:
        """
        JSON connector doesn't require active connection.

        This method exists for interface compatibility but does nothing.
        """
        pass

    def read(self, file_path: str, **kwargs) -> Iterator[Dict[str, Any]]:
        """
        Read JSON file and yield rows as dictionaries.

        Args:
            file_path: Path to JSON file
            **kwargs: Additional read options

        Yields:
            Dictionary representing a row with column names as keys
        """
        format = kwargs.get('format', 'json')

        if format == 'jsonl':
            yield from self.read_jsonl(file_path)
        else:
            yield from self.read_json(file_path)

    def validate(self, file_path: str, **kwargs) -> bool:
        """
        Validate JSON file.

        Args:
            file_path: Path to JSON file
            **kwargs: Additional validation options

        Returns:
            True if valid

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is not valid JSON
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"JSON file not found: {file_path}")

        if path.suffix.lower() not in ['.json', '.jsonl']:
            raise ValueError(f"Not a valid JSON file: {file_path}")

        # Try to parse JSON to validate
        try:
            with open(file_path, 'r', encoding=self.encoding) as f:
                if path.suffix.lower() == '.jsonl':
                    # Validate first line only for JSONL
                    first_line = f.readline().strip()
                    if first_line:
                        json.loads(first_line)
                else:
                    # Validate entire JSON file
                    json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON file: {e}")

        return True

    def get_metadata(self, file_path: str, **kwargs) -> Dict[str, Any]:
        """
        Get JSON file metadata.

        Args:
            file_path: Path to JSON file

        Returns:
            Dictionary with file statistics
        """
        path = Path(file_path)
        stats = path.stat()

        # Get row count
        rows = list(self.read(file_path))

        return {
            'file_path': str(path),
            'file_size': stats.st_size,
            'row_count': len(rows),
            'column_count': len(rows[0]) if rows else 0,
            'columns': list(rows[0].keys()) if rows else []
        }

    def read_json(self, file_path: str) -> Iterator[Dict[str, Any]]:
        """
        Read JSON file and yield rows as dictionaries.

        Args:
            file_path: Path to JSON file

        Yields:
            Dictionary representing a row
        """
        with open(file_path, 'r', encoding=self.encoding) as f:
            data = json.load(f)

            if isinstance(data, list):
                # Array of objects
                for item in data:
                    if isinstance(item, dict):
                        yield self._flatten_dict(item)
                    elif isinstance(item, (str, int, float, bool, type(None))):
                        # Primitive value - wrap in dict
                        yield {'value': item}
                    else:
                        # Nested array - convert to string
                        yield {'value': json.dumps(item)}
            elif isinstance(data, dict):
                # Single object
                yield self._flatten_dict(data)
            else:
                # Primitive value
                yield {'value': data}

    def read_jsonl(self, file_path: str) -> Iterator[Dict[str, Any]]:
        """
        Read JSON Lines file and yield rows as dictionaries.

        Args:
            file_path: Path to JSONL file

        Yields:
            Dictionary representing a row
        """
        with open(file_path, 'r', encoding=self.encoding) as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue  # Skip empty lines

                try:
                    data = json.loads(line)
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse line {line_num}: {e}")
                    continue

                if isinstance(data, dict):
                    yield self._flatten_dict(data)
                elif isinstance(data, (str, int, float, bool, type(None))):
                    yield {'value': data}
                else:
                    yield {'value': json.dumps(data)}

    def _flatten_dict(self, d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
        """
        Flatten nested dictionary structure.

        Args:
            d: Dictionary to flatten
            parent_key: Parent key for nested structures
            sep: Separator for nested keys

        Returns:
            Flattened dictionary
        """
        items = {}

        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k

            if isinstance(v, dict):
                # Recursively flatten nested dictionaries
                items.update(self._flatten_dict(v, new_key, sep=sep))
            elif isinstance(v, list):
                # Convert lists to JSON string
                items[new_key] = json.dumps(v)
            else:
                items[new_key] = v

        return items


# Register connector
from . import register_connector
register_connector('json', JSONConnector)
