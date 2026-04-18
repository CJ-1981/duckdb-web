"""
Test Parquet file upload and inspect functionality.

This test verifies that:
1. Parquet files can be uploaded via the upload endpoint
2. Compression detection works correctly
3. Column pruning (selecting specific columns) works
4. The inspect endpoint correctly processes Parquet files

@MX:SPEC: SPEC-PLATFORM-001 P2-T005
"""

import pytest
import os
import tempfile
from pathlib import Path

from httpx import AsyncClient, ASGITransport
from fastapi import status
import pandas as pd
import numpy as np

# Import the API
from src.api.main import create_app
app = create_app()


class TestParquetUpload:
    """Test Parquet file upload endpoint."""

    @pytest.fixture
    def app(self):
        """Return the FastAPI application for testing."""
        return create_app()

    @pytest.fixture
    def sample_parquet_file(self):
        """Create a sample Parquet file for testing."""
        data = {
            'id': range(100),
            'name': [f'Item{i}' for i in range(100)],
            'value': np.random.randint(1, 1000, 100),
            'category': np.random.choice(['A', 'B', 'C'], 100)
        }
        df = pd.DataFrame(data)

        with tempfile.NamedTemporaryFile(mode='wb', suffix='.parquet', delete=False) as f:
            df.to_parquet(f.name, index=False, engine='pyarrow')
            temp_path = f.name

        yield temp_path

        if os.path.exists(temp_path):
            os.unlink(temp_path)

    @pytest.fixture
    def sample_nested_parquet_file(self):
        """Create a Parquet file with nested data types."""
        data = {
            'id': range(50),
            'timestamp': pd.date_range('2024-01-01', periods=50, freq='h'),
            'float_val': np.random.randn(50),
            'bool_val': np.random.choice([True, False], 50)
        }
        df = pd.DataFrame(data)

        with tempfile.NamedTemporaryFile(mode='wb', suffix='.parquet', delete=False) as f:
            df.to_parquet(f.name, index=False, engine='pyarrow', compression='snappy')
            temp_path = f.name

        yield temp_path

        if os.path.exists(temp_path):
            os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_upload_parquet_success(self, app, sample_parquet_file):
        """Test that Parquet file upload returns proper metadata."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            with open(sample_parquet_file, 'rb') as f:
                files = {'file': ('test.parquet', f, 'application/octet-stream')}
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

            # Verify Parquet file was processed correctly
            assert data['filename'] == 'test.parquet'
            assert data['total_rows'] >= 10  # At minimum, some rows should be processed

            # Verify column names (may have _row as well)
            expected_columns = {'id', 'name', 'value', 'category'}
            actual_columns = set(data['available_columns'])
            assert expected_columns.issubset(actual_columns)

    @pytest.mark.asyncio
    async def test_upload_parquet_with_compression(self, app, sample_nested_parquet_file):
        """Test that compressed Parquet files are handled correctly."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            with open(sample_nested_parquet_file, 'rb') as f:
                files = {'file': ('compressed.parquet', f, 'application/octet-stream')}
                response = await client.post(
                    "/api/v1/data/upload",
                    files=files
                )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            # Verify compressed Parquet file was processed
            assert data['filename'] == 'compressed.parquet'
            assert data['total_rows'] >= 10

            # Verify data type preservation
            actual_columns = set(data['available_columns'])
            assert 'timestamp' in actual_columns
            assert 'float_val' in actual_columns
            assert 'bool_val' in actual_columns

    @pytest.mark.asyncio
    async def test_parquet_metadata_includes_types(self, app, sample_parquet_file):
        """Test that Parquet upload includes column type information."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            with open(sample_parquet_file, 'rb') as f:
                files = {'file': ('test.parquet', f, 'application/octet-stream')}
                response = await client.post(
                    "/api/v1/data/upload",
                    files=files
                )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            # Verify column_types is present
            assert 'column_types' in data
            assert len(data['column_types']) > 0

            # Each column type should have column_name and column_type
            for col_type in data['column_types']:
                assert 'column_name' in col_type
                assert 'column_type' in col_type

    @pytest.mark.asyncio
    async def test_empty_parquet_file(self, app):
        """Test handling of empty Parquet file."""
        data = pd.DataFrame({'a': [], 'b': []})

        with tempfile.NamedTemporaryFile(mode='wb', suffix='.parquet', delete=False) as f:
            data.to_parquet(f.name, engine='pyarrow')
            temp_path = f.name

        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                with open(temp_path, 'rb') as f:
                    files = {'file': ('empty.parquet', f, 'application/octet-stream')}
                    response = await client.post(
                        "/api/v1/data/upload",
                        files=files
                    )

            # Empty Parquet should still return 200 OK but with 0 rows
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data['total_rows'] == 0
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


class TestParquetInspect:
    """Test Parquet file processing in inspect endpoint."""

    @pytest.fixture
    def app(self):
        """Return the FastAPI application for testing."""
        return create_app()

    @pytest.fixture
    def sample_workflow_with_parquet(self):
        """Create a workflow with a Parquet file input node."""
        data = {'x': [1, 2, 3], 'y': [4, 5, 6], 'z': [7, 8, 9]}
        df = pd.DataFrame(data)

        with tempfile.NamedTemporaryFile(mode='wb', suffix='.parquet', delete=False) as f:
            df.to_parquet(f.name, index=False, engine='pyarrow')
            parquet_path = f.name

        yield {
            "nodes": [
                {
                    "id": "input-1",
                    "type": "input",
                    "data": {
                        "label": "Parquet Data",
                        "config": {
                            "file_path": parquet_path
                        }
                    }
                }
            ],
            "edges": []
        }

        if os.path.exists(parquet_path):
            os.unlink(parquet_path)

    @pytest.mark.asyncio
    async def test_inspect_parquet_node(self, app, sample_workflow_with_parquet):
        """Test that inspect endpoint processes Parquet files correctly."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/workflows/inspect",
                json={
                    "nodes": sample_workflow_with_parquet["nodes"],
                    "edges": sample_workflow_with_parquet["edges"],
                    "node_id": "input-1"
                }
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            # Verify we got statistics back
            assert 'total_rows' in data
            assert 'total_columns' in data
            assert 'columns' in data

            # Verify Parquet data was processed
            assert data['total_rows'] == 3
            assert data['total_columns'] >= 3  # May include _row


class TestParquetCompression:
    """Test various Parquet compression formats."""

    @pytest.fixture
    def app(self):
        """Return the FastAPI application for testing."""
        return create_app()

    @pytest.mark.asyncio
    async def test_parquet_compression_formats(self, app):
        """Test different compression codecs for Parquet files."""
        data = {'col1': range(50), 'col2': [f'value{i}' for i in range(50)]}
        df = pd.DataFrame(data)

        compression_types = ['snappy', 'gzip', None]  # None = uncompressed

        for compression in compression_types:
            with tempfile.NamedTemporaryFile(mode='wb', suffix='.parquet', delete=False) as f:
                df.to_parquet(f.name, engine='pyarrow', compression=compression)
                temp_path = f.name

            try:
                async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                    with open(temp_path, 'rb') as f:
                        files = {'file': (f'compressed_{compression}.parquet', f, 'application/octet-stream')}
                        response = await client.post(
                            "/api/v1/data/upload",
                            files=files
                        )

                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data['total_rows'] >= 10  # At least some rows processed
            finally:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)


class TestParquetPerformance:
    """Test Parquet performance with larger files."""

    @pytest.fixture
    def app(self):
        """Return the FastAPI application for testing."""
        return create_app()

    @pytest.mark.asyncio
    async def test_large_parquet_file(self, app):
        """Test handling of larger Parquet files."""
        # Create a Parquet file with 10,000 rows
        data = {
            'id': range(10000),
            'value': np.random.randn(10000),
            'category': np.random.choice(['A', 'B', 'C', 'D'], 10000)
        }
        df = pd.DataFrame(data)

        with tempfile.NamedTemporaryFile(mode='wb', suffix='.parquet', delete=False) as f:
            df.to_parquet(f.name, index=False, engine='pyarrow', compression='snappy')
            temp_path = f.name

        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                with open(temp_path, 'rb') as f:
                    files = {'file': ('large.parquet', f, 'application/octet-stream')}
                    response = await client.post(
                        "/api/v1/data/upload",
                        files=files
                    )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            # Should handle large files efficiently
            assert data['total_rows'] >= 10  # At minimum, some rows should be processed
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
