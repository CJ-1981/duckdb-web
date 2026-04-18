"""Test multi-sheet Excel upload and sheet selection"""

import pytest
import tempfile
from pathlib import Path
import pandas as pd

from src.core.processor import Processor
from src.core.connectors.excel import ExcelConnector


def test_excel_get_sheet_names():
    """Test getting sheet names from multi-sheet Excel file"""
    # Create a multi-sheet Excel file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.xlsx', delete=False) as f:
        temp_name = f.name

    try:
        # Create Excel file with multiple sheets
        with pd.ExcelWriter(temp_name, engine='openpyxl') as writer:
            # Sheet 1: Sales data
            df1 = pd.DataFrame({
                'id': [1, 2, 3],
                'product': ['A', 'B', 'C'],
                'amount': [100, 200, 300]
            })
            df1.to_excel(writer, sheet_name='Sales', index=False)

            # Sheet 2: Inventory data
            df2 = pd.DataFrame({
                'item': ['X', 'Y', 'Z'],
                'quantity': [10, 20, 30],
                'location': ['NY', 'LA', 'CHI']
            })
            df2.to_excel(writer, sheet_name='Inventory', index=False)

            # Sheet 3: HR data
            df3 = pd.DataFrame({
                'employee': ['John', 'Jane', 'Bob'],
                'department': ['Sales', 'IT', 'HR'],
                'salary': [50000, 60000, 45000]
            })
            df3.to_excel(writer, sheet_name='HR', index=False)

        # Test getting sheet names
        connector = ExcelConnector()
        sheet_names = connector.get_sheet_names(temp_name)

        assert len(sheet_names) == 3
        assert 'Sales' in sheet_names
        assert 'Inventory' in sheet_names
        assert 'HR' in sheet_names

        # Test loading specific sheet
        processor = Processor()

        # Load Sales sheet
        df_sales = processor.load_excel(temp_name, sheet_name='Sales')
        # Note: Processor adds _row column automatically
        assert 'id' in df_sales.columns
        assert 'product' in df_sales.columns
        assert 'amount' in df_sales.columns
        assert len(df_sales) == 3

        # Load Inventory sheet
        processor2 = Processor()
        df_inventory = processor2.load_excel(temp_name, sheet_name='Inventory')
        assert 'item' in df_inventory.columns
        assert 'quantity' in df_inventory.columns
        assert 'location' in df_inventory.columns
        assert len(df_inventory) == 3

    finally:
        Path(temp_name).unlink(missing_ok=True)


def test_excel_metadata_includes_sheet_names():
    """Test that get_metadata returns sheet names"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.xlsx', delete=False) as f:
        temp_name = f.name

    try:
        # Create Excel file with multiple sheets
        with pd.ExcelWriter(temp_name, engine='openpyxl') as writer:
            df1 = pd.DataFrame({'a': [1, 2], 'b': [3, 4]})
            df1.to_excel(writer, sheet_name='Sheet1', index=False)

            df2 = pd.DataFrame({'x': [10], 'y': [20]})
            df2.to_excel(writer, sheet_name='Sheet2', index=False)

        connector = ExcelConnector()
        metadata = connector.get_metadata(temp_name)

        assert 'sheet_names' in metadata
        assert metadata['sheet_names'] == ['Sheet1', 'Sheet2']
        assert metadata['selected_sheet'] == 'Sheet1'
        assert metadata['row_count'] == 2

    finally:
        Path(temp_name).unlink(missing_ok=True)
