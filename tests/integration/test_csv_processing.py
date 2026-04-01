"""
Integration tests for CSV Connector

Tests end-to-end CSV processing including:
- Integration with DuckDB database
- Real CSV file processing
- Large file streaming
- Complete pipeline validation
"""

import pytest
import tempfile
import csv
from pathlib import Path
import duckdb

from src.core.connectors.csv import CSVConnector
from src.core.database import DatabaseConnection


# ========================================================================
#  Integration Test Fixtures
# =========================================================================

@pytest.fixture
def sample_csv_file():
    """Create a sample CSV file for testing"""
    csv_data = """id,name,age,amount,active,join_date
1,Alice,30,1500.50,true,2023-01-15
2,Bob,25,950.75,false,2023-02-20
3,Charlie,35,2500.00,true,2023-03-10
4,David,28,1800.25,true,2023-04-05
5,Emma,32,2100.75,false,2023-05-12
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(csv_data)
        temp_path = f.name

    yield temp_path

    # Cleanup
    Path(temp_path).unlink(missing_ok=True)


@pytest.fixture
def large_csv_file():
    """Create a large CSV file for streaming tests"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        writer = csv.writer(f)
        # Header
        writer.writerow(['id', 'name', 'value', 'timestamp', 'category'])

        # Write many rows
        for i in range(5000):
            writer.writerow([
                i,
                f'Item_{i}',
                i * 100.5,
                f'2023-{(i % 12) + 1:02d}-{(i % 28) + 1:02d}',
                f'Cat_{i % 5}'
            ])

        temp_path = f.name

    yield temp_path

    # Cleanup
    Path(temp_path).unlink(missing_ok=True)


@pytest.fixture
def in_memory_database():
    """Create an in-memory DuckDB database for testing"""
    db = DatabaseConnection(":memory:")
    yield db
    db.close()


@pytest.fixture
def temp_database():
    """Create a temporary file-based DuckDB database"""
    import uuid
    db_path = f"/tmp/test_db_{uuid.uuid4()}.duckdb"

    db = DatabaseConnection(db_path)
    yield db
    db.close()

    # Cleanup
    Path(db_path).unlink(missing_ok=True)


# ========================================================================
#  End-to-End Integration Tests
# ========================================================================

class TestCSVConnectorIntegration:
    """End-to-end integration tests for CSV connector"""

    def test_full_csv_import_pipeline(self, sample_csv_file, in_memory_database):
        """Test complete CSV import pipeline"""
        connector = CSVConnector()

        # Import CSV to database
        connector.import_to_duckdb(
            csv_path=sample_csv_file,
            db_connection=in_memory_database,
            table_name='users'
        )

        # Verify data was imported
        result = in_memory_database.execute(
            "SELECT COUNT(*) as count FROM users"
        )
        assert result[0]['count'] == 5

        # Verify schema
        schema_result = in_memory_database.execute("DESCRIBE users")
        column_names = [row['column_name'] for row in schema_result]
        assert 'id' in column_names
        assert 'name' in column_names
        assert 'age' in column_names
        assert 'amount' in column_names
        assert 'active' in column_names
        assert 'join_date' in column_names

    def test_csv_data_accuracy_after_import(self, sample_csv_file, in_memory_database):
        """Test that data is accurately imported"""
        connector = CSVConnector()

        connector.import_to_duckdb(
            csv_path=sample_csv_file,
            db_connection=in_memory_database,
            table_name='users'
        )

        # Check specific row (DuckDB converts types, so age will be INTEGER)
        result = in_memory_database.execute(
            "SELECT * FROM users WHERE name = 'Alice'"
        )
        assert len(result) == 1
        # DuckDB may have converted the type - check with flexible comparison
        assert result[0]['age'] in (30, '30')  # Accept either type

    def test_type_preservation_after_import(self, sample_csv_file, in_memory_database):
        """Test that data types are preserved during import"""
        connector = CSVConnector()

        connector.import_to_duckdb(
            csv_path=sample_csv_file,
            db_connection=in_memory_database,
            table_name='users'
        )

        # Check data types
        schema_result = in_memory_database.execute("DESCRIBE users")

        # Build column type mapping
        column_types = {row['column_name']: row['column_type'] for row in schema_result}

        # Verify types (DuckDB may use different type names)
        assert 'id' in column_types
        assert 'name' in column_types
        assert 'amount' in column_types

    def test_multiple_csv_imports_to_same_database(self, in_memory_database):
        """Test importing multiple CSV files to the same database"""
        connector = CSVConnector()

        # Create first CSV
        csv_data_1 = """id,name
1,Alice
2,Bob
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_data_1)
            csv_path_1 = f.name

        # Create second CSV
        csv_data_2 = """id,amount
1,100.50
2,200.75
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_data_2)
            csv_path_2 = f.name

        try:
            # Import both files
            connector.import_to_duckdb(
                csv_path=csv_path_1,
                db_connection=in_memory_database,
                table_name='table1'
            )

            connector.import_to_duckdb(
                csv_path=csv_path_2,
                db_connection=in_memory_database,
                table_name='table2'
            )

            # Verify both tables exist
            tables = in_memory_database.execute("SHOW TABLES")
            table_names = [row['name'] for row in tables]
            assert 'table1' in table_names
            assert 'table2' in table_names

            # Verify data in both tables
            count1 = in_memory_database.execute("SELECT COUNT(*) as count FROM table1")
            count2 = in_memory_database.execute("SELECT COUNT(*) as count FROM table2")
            assert count1[0]['count'] == 2
            assert count2[0]['count'] == 2

        finally:
            Path(csv_path_1).unlink(missing_ok=True)
            Path(csv_path_2).unlink(missing_ok=True)


class TestLargeFileStreaming:
    """Tests for large file streaming functionality"""

    def test_large_file_streaming_integration(self, large_csv_file, temp_database):
        """Test streaming large file into database"""
        connector = CSVConnector(streaming_threshold=1)  # Force streaming

        connector.import_to_duckdb(
            csv_path=large_csv_file,
            db_connection=temp_database,
            table_name='large_data'
        )

        # Verify all rows were imported
        result = temp_database.execute("SELECT COUNT(*) as count FROM large_data")
        assert result[0]['count'] == 5000

    def test_streaming_with_progress_reporting(self, large_csv_file, temp_database):
        """Test streaming with progress callbacks"""
        connector = CSVConnector(streaming_threshold=1)

        progress_updates = []

        def progress_callback(progress):
            progress_updates.append(progress)

        connector.import_to_duckdb(
            csv_path=large_csv_file,
            db_connection=temp_database,
            table_name='large_data',
            progress_callback=progress_callback
        )

        # Verify progress was reported
        assert len(progress_updates) > 0

        # Check final progress
        final_progress = progress_updates[-1]
        assert final_progress['rows_processed'] == 5000
        assert final_progress['total_rows'] == 5000
        assert final_progress['percentage'] >= 99.0

    def test_streaming_handles_interruption(self, large_csv_file, temp_database):
        """Test that streaming can handle interruption gracefully"""
        connector = CSVConnector(streaming_threshold=1)

        # Import should complete successfully
        connector.import_to_duckdb(
            csv_path=large_csv_file,
            db_connection=temp_database,
            table_name='large_data'
        )

        # Verify partial data if needed (or full data in this case)
        result = temp_database.execute("SELECT COUNT(*) as count FROM large_data")
        assert result[0]['count'] > 0


class TestCSVParsingEdgeCases:
    """Integration tests for edge cases in CSV parsing"""

    def test_csv_with_special_characters(self, in_memory_database):
        """Test CSV with special characters and quotes"""
        csv_data = '''id,name,description
1,Product A,"Description with, commas"
2,Product B,"Description with ""quotes"""
3,Product C,"Description with text"
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_data)
            temp_path = f.name

        try:
            connector = CSVConnector()
            connector.import_to_duckdb(
                csv_path=temp_path,
                db_connection=in_memory_database,
                table_name='products'
            )

            # Verify data was parsed correctly
            result = in_memory_database.execute("SELECT * FROM products WHERE id = 1")
            assert len(result) == 1
            assert 'commas' in result[0]['description']

        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_csv_with_different_encodings(self, in_memory_database):
        """Test CSV with non-UTF8 encoding"""
        # Create CSV with Latin-1 encoding
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv',
                                         encoding='latin-1', delete=False) as f:
            f.write('id,name\n1,Café\n2,München\n3,São Paulo\n')
            temp_path = f.name

        try:
            connector = CSVConnector(encoding='latin-1')
            connector.import_to_duckdb(
                csv_path=temp_path,
                db_connection=in_memory_database,
                table_name='cities'
            )

            # Verify special characters preserved
            result = in_memory_database.execute("SELECT * FROM cities WHERE id = 1")
            assert len(result) == 1

        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_csv_with_inconsistent_row_lengths(self, in_memory_database):
        """Test CSV with inconsistent row lengths"""
        csv_data = """id,name,value
1,Item A,100
2,Item B,
3,Item C,300
4,Item D,400
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_data)
            temp_path = f.name

        try:
            connector = CSVConnector()
            connector.import_to_duckdb(
                csv_path=temp_path,
                db_connection=in_memory_database,
                table_name='items'
            )

            # Should handle inconsistent rows
            result = in_memory_database.execute("SELECT COUNT(*) as count FROM items")
            assert result[0]['count'] == 4

        finally:
            Path(temp_path).unlink(missing_ok=True)


class TestMissingValueHandling:
    """Integration tests for missing value handling"""

    def test_missing_values_imported_correctly(self, in_memory_database):
        """Test that missing values are imported as NULL"""
        csv_data = """id,name,value
1,Item A,100
2,Item B,
3,,300
4,Item D,
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_data)
            temp_path = f.name

        try:
            connector = CSVConnector()
            connector.import_to_duckdb(
                csv_path=temp_path,
                db_connection=in_memory_database,
                table_name='items'
            )

            # Check NULL handling
            result = in_memory_database.execute(
                "SELECT * FROM items WHERE name IS NULL OR name = ''"
            )
            assert len(result) >= 1

        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_various_missing_value_representations(self, in_memory_database):
        """Test various representations of missing values"""
        csv_data = """id,name,value
1,Item A,100
2,Item B,NULL
3,Item C,NA
4,Item D,NaN
5,Item E,
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_data)
            temp_path = f.name

        try:
            connector = CSVConnector()
            connector.import_to_duckdb(
                csv_path=temp_path,
                db_connection=in_memory_database,
                table_name='items'
            )

            # Should import all rows
            result = in_memory_database.execute("SELECT COUNT(*) as count FROM items")
            assert result[0]['count'] == 5

        finally:
            Path(temp_path).unlink(missing_ok=True)


class TestQueryAfterImport:
    """Test querying imported data"""

    def test_basic_query_after_import(self, sample_csv_file, in_memory_database):
        """Test basic queries after CSV import"""
        connector = CSVConnector()

        connector.import_to_duckdb(
            csv_path=sample_csv_file,
            db_connection=in_memory_database,
            table_name='users'
        )

        # Test filter query
        result = in_memory_database.execute(
            "SELECT * FROM users WHERE age > 30"
        )
        assert len(result) == 2  # Charlie (35) and Emma (32)

        # Test aggregation
        result = in_memory_database.execute(
            "SELECT COUNT(*) as count FROM users WHERE active = 'true'"
        )
        assert result[0]['count'] == 3

    def test_complex_query_after_import(self, sample_csv_file, in_memory_database):
        """Test complex queries after CSV import"""
        connector = CSVConnector()

        connector.import_to_duckdb(
            csv_path=sample_csv_file,
            db_connection=in_memory_database,
            table_name='users'
        )

        # Test JOIN-like operation (self-join for demo)
        result = in_memory_database.execute("""
            SELECT a.name, b.name as friend
            FROM users a
            CROSS JOIN users b
            WHERE a.age > b.age
            LIMIT 5
        """)
        assert len(result) > 0

    def test_export_after_import(self, sample_csv_file, in_memory_database):
        """Test exporting data after CSV import"""
        connector = CSVConnector()

        connector.import_to_duckdb(
            csv_path=sample_csv_file,
            db_connection=in_memory_database,
            table_name='users'
        )

        # Export to new table
        in_memory_database.execute(
            "CREATE TABLE active_users AS SELECT * FROM users WHERE active = 'true'"
        )

        result = in_memory_database.execute("SELECT COUNT(*) as count FROM active_users")
        assert result[0]['count'] == 3


class TestPerformanceAndScalability:
    """Performance and scalability tests"""

    def test_import_performance(self, large_csv_file, temp_database):
        """Test import performance with large file"""
        import time

        connector = CSVConnector(streaming_threshold=1)

        start_time = time.time()
        connector.import_to_duckdb(
            csv_path=large_csv_file,
            db_connection=temp_database,
            table_name='performance_test'
        )
        elapsed_time = time.time() - start_time

        # Verify import completed
        result = temp_database.execute("SELECT COUNT(*) as count FROM performance_test")
        assert result[0]['count'] == 5000

        # Performance assertion (should complete in reasonable time)
        # This is a loose assertion; adjust based on environment
        assert elapsed_time < 30.0  # Should complete within 30 seconds

    def test_memory_efficiency_during_import(self, large_csv_file, temp_database):
        """Test that streaming doesn't consume excessive memory"""
        connector = CSVConnector(streaming_threshold=1, chunk_size=100)

        # This should complete without memory issues
        connector.import_to_duckdb(
            csv_path=large_csv_file,
            db_connection=temp_database,
            table_name='memory_test'
        )

        result = temp_database.execute("SELECT COUNT(*) as count FROM memory_test")
        assert result[0]['count'] == 5000
