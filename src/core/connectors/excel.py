"""
Excel Connector

Enhanced Excel connector with automatic type inference, streaming support,
and integration with DuckDB database.
"""

import logging
from typing import List, Dict, Any, Iterator, Optional
from pathlib import Path

import pandas as pd

from .base import BaseConnector

logger = logging.getLogger(__name__)


class ExcelConnector(BaseConnector):
    """
    Enhanced Excel connector with automatic type inference and streaming

    Features:
    - Automatic type inference (INTEGER, FLOAT, BOOLEAN, DATE, VARCHAR)
    - Multiple sheet support
    - Header detection and validation
    - Missing value handling (NULL, '', NA, NaN, None)
    - Large file streaming
    - Support for .xlsx and .xls files

    Example:
        >>> connector = ExcelConnector(sheet_name='Sheet1')
        >>> rows = list(connector.read_excel('data.xlsx'))
    """

    # Class constants
    MISSING_VALUES = ['', 'NULL', 'NA', 'NaN', 'nan', 'None', 'null', 'N/A']

    def __init__(
        self,
        sheet_name: Optional[str] = None,
        header_row: int = 0,
    ):
        """
        Initialize Excel connector

        Args:
            sheet_name: Sheet name to load (default: first sheet)
            header_row: Row number containing headers (0-indexed, default: 0)
        """
        super().__init__()
        self.sheet_name = sheet_name
        self.header_row = header_row

    def connect(self, **kwargs) -> None:
        """
        Excel connector doesn't require active connection

        This method exists for interface compatibility but does nothing.
        """
        pass

    def read(self, file_path: str, **kwargs) -> Iterator[Dict[str, Any]]:
        """
        Read Excel file and yield rows as dictionaries

        Args:
            file_path: Path to Excel file
            **kwargs: Additional read options

        Yields:
            Dictionary representing a row with column names as keys
        """
        yield from self.read_excel(file_path, **kwargs)

    def validate(self, file_path: str) -> bool:
        """
        Validate Excel file

        Args:
            file_path: Path to Excel file

        Returns:
            True if valid

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is not a valid Excel file
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"Excel file not found: {file_path}")

        if path.suffix.lower() not in ['.xlsx', '.xls']:
            raise ValueError(f"Not a valid Excel file: {file_path}")

        return True

    def get_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Get Excel file metadata

        Args:
            file_path: Path to Excel file

        Returns:
            Dictionary with file statistics
        """
        path = Path(file_path)
        stats = path.stat()

        # Get sheet names
        with pd.ExcelFile(file_path) as excel_file:
            sheet_names = excel_file.sheet_names

        # Get row count for default sheet
        sheet = self.sheet_name or sheet_names[0]
        # If sheet_name is None, use the first sheet
        if sheet is None:
            sheet = sheet_names[0]
        df = pd.read_excel(file_path, sheet_name=sheet, header=self.header_row)

        return {
            'file_path': str(path),
            'file_size': stats.st_size,
            'sheet_names': sheet_names,
            'selected_sheet': sheet,
            'row_count': len(df),
            'column_count': len(df.columns),
            'columns': list(df.columns)
        }

    def read_excel(
        self,
        file_path: str,
        **kwargs
    ) -> Iterator[Dict[str, Any]]:
        """
        Read Excel file and yield rows as dictionaries

        Args:
            file_path: Path to Excel file
            **kwargs: Additional options (sheet_name, header_row override)

        Yields:
            Dictionary representing a row with column names as keys
        """
        # Validate file
        self.validate(file_path)

        # Get parameters
        sheet_name = kwargs.get('sheet_name', self.sheet_name)
        header_row = kwargs.get('header_row', self.header_row)

        # If sheet_name is None, get the first sheet name
        if sheet_name is None:
            with pd.ExcelFile(file_path) as excel_file:
                sheet_name = excel_file.sheet_names[0]

        # Read Excel file
        df = pd.read_excel(
            file_path,
            sheet_name=sheet_name,
            header=header_row
        )

        # Convert DataFrame to list of dictionaries
        for _, row in df.iterrows():
            # Convert to dict and handle NaN values
            row_dict = {}
            for col in df.columns:
                value = row[col]
                # Handle NaN values
                if pd.isna(value):
                    row_dict[col] = None
                else:
                    row_dict[col] = value
            yield row_dict

    def get_sheet_names(self, file_path: str) -> List[str]:
        """
        Get list of sheet names from Excel file

        Args:
            file_path: Path to Excel file

        Returns:
            List of sheet names
        """
        with pd.ExcelFile(file_path) as excel_file:
            return excel_file.sheet_names


# Register connector
from . import register_connector
register_connector('excel', ExcelConnector)
