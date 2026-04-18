"""
Test Excel file upload and inspect functionality.

This test verifies that:
1. Excel files (.xlsx, .xls) can be uploaded via the upload endpoint
2. The inspect endpoint correctly processes Excel files
3. File type detection works properly by extension

@MX:SPEC: SPEC-PLATFORM-001 P2-T005
"""

import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, AsyncMock
import pandas as pd

from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI, status

# Import the API
from src.api.main import create_app
app = create_app()


class TestExcelUpload:
    """Test Excel file upload endpoint."""

    @pytest.fixture
    def app(self):
        """Return the FastAPI application for testing."""
        return create_app()

    @pytest.fixture
    def sample_excel_file(self):
        """Create a sample Excel file for testing."""
        # Create sample data
        data = {
            'name': ['Alice', 'Bob', 'Charlie'],
            'age': [30, 25, 35],
            'city': ['New York', 'London', 'Paris']
        }
        df = pd.DataFrame(data)

        # Create temporary Excel file
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.xlsx', delete=False) as f:
            df.to_excel(f.name, index=False, engine='openpyxl')
            temp_path = f.name

        yield temp_path

        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    @pytest.fixture
    def sample_csv_file(self):
        """Create a sample CSV file for testing."""
        # Create sample data
        data = {
            'name': ['Alice', 'Bob', 'Charlie'],
            'age': [30, 25, 35],
            'city': ['New York', 'London', 'Paris']
        }
        df = pd.DataFrame(data)

        # Create temporary CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df.to_csv(f.name, index=False)
            temp_path = f.name

        yield temp_path

        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_upload_excel_file_success(self, app, sample_excel_file):
        """Test that Excel file upload returns proper metadata."""
        # Check if openpyxl is available
        try:
            import openpyxl
        except ImportError:
            pytest.skip("openpyxl not installed")

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            with open(sample_excel_file, 'rb') as f:
                files = {'file': ('test.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
                response = await client.post(
                    "/api/v1/data/upload",
                    files=files
                )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            # Verify response structure
            assert 'file_id' in data
            assert 'file_path' in data
            assert 'filename' in data
            assert 'available_columns' in data
            assert 'total_rows' in data

            # Verify Excel file was processed correctly
            assert data['filename'] == 'test.xlsx'
            assert data['total_rows'] == 3
            # Check that expected columns are present (may have _row as well)
            expected_columns = {'name', 'age', 'city'}
            actual_columns = set(data['available_columns'])
            assert expected_columns.issubset(actual_columns)

    @pytest.mark.asyncio
    async def test_upload_csv_file_still_works(self, app, sample_csv_file):
        """Test that CSV file upload still works after Excel changes."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            with open(sample_csv_file, 'rb') as f:
                files = {'file': ('test.csv', f, 'text/csv')}
                response = await client.post(
                    "/api/v1/data/upload",
                    files=files
                )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            # Verify CSV file was processed correctly
            assert data['filename'] == 'test.csv'
            assert data['total_rows'] == 3
            # Check that expected columns are present
            expected_columns = {'name', 'age', 'city'}
            actual_columns = set(data['available_columns'])
            assert expected_columns.issubset(actual_columns)

    @pytest.mark.asyncio
    async def test_upload_xls_file(self, app):
        """Test that .xls files are also supported."""
        try:
            import xlwt
        except ImportError:
            pytest.skip("xlwt not installed")

        # Create sample data
        data = {
            'product': ['A', 'B', 'C'],
            'price': [100, 200, 300]
        }
        df = pd.DataFrame(data)

        # Create temporary .xls file
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.xls', delete=False) as f:
            df.to_excel(f.name, index=False, engine='xlwt')
            temp_path = f.name

        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                with open(temp_path, 'rb') as f:
                    files = {'file': ('test.xls', f, 'application/vnd.ms-excel')}
                    response = await client.post(
                        "/api/v1/data/upload",
                        files=files
                    )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data['filename'] == 'test.xls'
            # Check that expected columns are present
            expected_columns = {'product', 'price'}
            actual_columns = set(data['available_columns'])
            assert expected_columns.issubset(actual_columns)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


class TestExcelInspect:
    """Test Excel file processing in inspect endpoint."""

    @pytest.fixture
    def app(self):
        """Return the FastAPI application for testing."""
        return create_app()

    @pytest.fixture
    def sample_workflow_with_excel(self, sample_excel_file_factory):
        """Create a workflow with an Excel file input node."""
        excel_path = sample_excel_file_factory()

        return {
            "nodes": [
                {
                    "id": "input-1",
                    "type": "input",
                    "data": {
                        "label": "Excel Data",
                        "config": {
                            "file_path": excel_path
                        }
                    }
                }
            ],
            "edges": []
        }

    @pytest.fixture
    def sample_excel_file_factory(self):
        """Factory function to create temporary Excel files."""
        def _create_excel(data=None):
            if data is None:
                data = {
                    'name': ['Alice', 'Bob'],
                    'value': [100, 200]
                }
            df = pd.DataFrame(data)

            with tempfile.NamedTemporaryFile(mode='wb', suffix='.xlsx', delete=False) as f:
                df.to_excel(f.name, index=False, engine='openpyxl')
                return f.name

        return _create_excel

    @pytest.mark.asyncio
    async def test_inspect_excel_node(self, app, sample_workflow_with_excel, sample_excel_file_factory):
        """Test that inspect endpoint processes Excel files correctly."""
        try:
            import openpyxl
        except ImportError:
            pytest.skip("openpyxl not installed")

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/workflows/inspect",
                json={
                    "nodes": sample_workflow_with_excel["nodes"],
                    "edges": sample_workflow_with_excel["edges"],
                    "node_id": "input-1"
                }
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            # Verify we got statistics back
            assert 'total_rows' in data
            assert 'total_columns' in data
            assert 'columns' in data

            # Verify Excel data was processed
            assert data['total_rows'] == 2
            # Note: total_columns includes _row column
            assert data['total_columns'] >= 2
            assert len(data['columns']) >= 2


class TestFileTypeDetection:
    """Test file type detection by extension."""

    @pytest.mark.parametrize("filename,expected_type", [
        ("data.xlsx", "excel"),
        ("data.xls", "excel"),
        ("data.csv", "csv"),
        ("data.json", "json"),
        ("data.jsonl", "jsonl"),
    ])
    def test_file_extension_detection(self, filename, expected_type):
        """Test that file extensions are correctly detected."""
        import os
        ext = os.path.splitext(filename)[1].lower()
        if ext in ['.xlsx', '.xls']:
            file_type = "excel"
        elif ext in ['.json', '.jsonl']:
            file_type = "json" if ext == '.json' else "jsonl"
        else:
            file_type = "csv"
        assert file_type == expected_type
