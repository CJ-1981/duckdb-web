"""
Integration tests for MySQL Connector

These tests require a running MySQL instance.
If MySQL is not available, these tests will be skipped.
"""

import pytest
from unittest.mock import patch, MagicMock
from typing import Optional

# Try to import MySQL dependencies
try:
    import pymysql
    PYMYSQL_AVAILABLE = True
except ImportError:
    try:
        import mysql.connector
        MYSQL_CONNECTOR_AVAILABLE = True
        PYMYSQL_AVAILABLE = False
    except ImportError:
        PYMYSQL_AVAILABLE = False
        MYSQL_CONNECTOR_AVAILABLE = False

from src.core.connectors.mysql import MySQLConnector
from src.core.connectors.database import DatabaseConnector


# ========================================================================
# Integration Test Configuration
# ========================================================================

@pytest.fixture(scope="module")
def mysql_config():
    """MySQL connection configuration for integration tests"""
    return {
        'host': 'localhost',
        'port': 3306,
        'database': 'test_db',
        'user': 'test_user',
        'password': 'test_password',
        'charset': 'utf8mb4',
    }


@pytest.fixture(scope="module")
def skip_if_no_mysql(mysql_config):
    """Skip tests if MySQL is not available"""
    if not (PYMYSQL_AVAILABLE or MYSQL_CONNECTOR_AVAILABLE):
        pytest.skip("Neither pymysql nor mysql-connector-python installed")

    # Try to connect to MySQL
    try:
        if PYMYSQL_AVAILABLE:
            conn = pymysql.connect(**mysql_config, connect_timeout=2)
        else:
            conn = mysql.connector.connect(**mysql_config, connection_timeout=2)
        conn.close()
    except Exception:
        pytest.skip("MySQL not available or cannot connect")


@pytest.fixture
def test_table_setup(mysql_config, skip_if_no_mysql):
    """
    Create test tables and data for integration tests.
    Clean up tables after tests complete.
    """
    if PYMYSQL_AVAILABLE:
        conn = pymysql.connect(**mysql_config)
    else:
        conn = mysql.connector.connect(**mysql_config)

    cursor = conn.cursor()

    # Create test table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS test_users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            age INT,
            active TINYINT(1) DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Insert test data
    cursor.execute("""
        INSERT INTO test_users (name, email, age, active)
        VALUES
            ('Alice', 'alice@example.com', 30, 1),
            ('Bob', 'bob@example.com', 25, 0),
            ('Charlie', 'charlie@example.com', 35, 1)
    """)

    conn.commit()

    yield conn

    # Cleanup
    cursor.execute("DROP TABLE IF EXISTS test_users")
    conn.commit()
    cursor.close()
    conn.close()


# ========================================================================
# Integration Tests (Real MySQL)
# ========================================================================

class TestMySQLConnectorRealConnection:
    """Integration tests with real MySQL database"""

    def test_connect_to_real_database(self, mysql_config, skip_if_no_mysql):
        """Test connecting to real MySQL database"""
        connector = MySQLConnector(**mysql_config)
        connector.connect()

        assert connector.connected is True

        connector.disconnect()

    def test_list_tables_from_real_database(
        self, mysql_config, skip_if_no_mysql, test_table_setup
    ):
        """Test listing tables from real database"""
        connector = MySQLConnector(**mysql_config)
        connector.connect()

        tables = connector.list_tables()

        assert 'test_users' in tables
        assert len(tables) >= 1

        connector.disconnect()

    def test_get_table_schema_from_real_database(
        self, mysql_config, skip_if_no_mysql, test_table_setup
    ):
        """Test getting table schema from real database"""
        connector = MySQLConnector(**mysql_config)
        connector.connect()

        schema = connector.get_table_schema('test_users')

        assert len(schema) == 6  # 6 columns

        # Check specific column
        id_column = next(col for col in schema if col['name'] == 'id')
        assert 'INT' in id_column['type']
        assert id_column['nullable'] is False

        connector.disconnect()

    def test_execute_select_on_real_database(
        self, mysql_config, skip_if_no_mysql, test_table_setup
    ):
        """Test executing SELECT query on real database"""
        connector = MySQLConnector(**mysql_config)
        connector.connect()

        results = connector.execute_select("SELECT * FROM test_users ORDER BY name")

        assert len(results) == 3
        assert results[0][1] == 'Alice'  # name column
        assert results[1][1] == 'Bob'
        assert results[2][1] == 'Charlie'

        connector.disconnect()

    def test_execute_insert_on_real_database(
        self, mysql_config, skip_if_no_mysql, test_table_setup
    ):
        """Test executing INSERT query on real database"""
        connector = MySQLConnector(**mysql_config)
        connector.connect()

        affected = connector.execute_insert(
            "INSERT INTO test_users (name, email, age) VALUES (%s, %s, %s)",
            params=['David', 'david@example.com', 28]
        )

        assert affected == 1

        # Verify insert
        results = connector.execute_select(
            "SELECT * FROM test_users WHERE email = %s",
            params=['david@example.com']
        )
        assert len(results) == 1
        assert results[0][1] == 'David'

        connector.disconnect()

    def test_execute_update_on_real_database(
        self, mysql_config, skip_if_no_mysql, test_table_setup
    ):
        """Test executing UPDATE query on real database"""
        connector = MySQLConnector(**mysql_config)
        connector.connect()

        affected = connector.execute_update(
            "UPDATE test_users SET age = %s WHERE name = %s",
            params=[31, 'Alice']
        )

        assert affected == 1

        # Verify update
        results = connector.execute_select(
            "SELECT age FROM test_users WHERE name = %s",
            params=['Alice']
        )
        assert results[0][0] == 31

        connector.disconnect()

    def test_execute_delete_on_real_database(
        self, mysql_config, skip_if_no_mysql, test_table_setup
    ):
        """Test executing DELETE query on real database"""
        connector = MySQLConnector(**mysql_config)
        connector.connect()

        affected = connector.execute_delete(
            "DELETE FROM test_users WHERE name = %s",
            params=['Bob']
        )

        assert affected == 1

        # Verify delete
        results = connector.execute_select(
            "SELECT * FROM test_users WHERE name = %s",
            params=['Bob']
        )
        assert len(results) == 0

        connector.disconnect()

    def test_transaction_commit_on_real_database(
        self, mysql_config, skip_if_no_mysql, test_table_setup
    ):
        """Test transaction commit on real database"""
        connector = MySQLConnector(**mysql_config)
        connector.connect()

        # Start transaction
        connector.begin_transaction()

        # Insert record
        connector.execute_insert(
            "INSERT INTO test_users (name, email, age) VALUES (%s, %s, %s)",
            params=['Eve', 'eve@example.com', 27]
        )

        # Commit transaction
        connector.commit_transaction()

        # Verify record exists
        results = connector.execute_select(
            "SELECT * FROM test_users WHERE email = %s",
            params=['eve@example.com']
        )
        assert len(results) == 1

        connector.disconnect()

    def test_transaction_rollback_on_real_database(
        self, mysql_config, skip_if_no_mysql, test_table_setup
    ):
        """Test transaction rollback on real database"""
        connector = MySQLConnector(**mysql_config)
        connector.connect()

        # Get initial count
        initial_count = len(connector.execute_select("SELECT * FROM test_users"))

        # Start transaction
        connector.begin_transaction()

        # Insert record
        connector.execute_insert(
            "INSERT INTO test_users (name, email, age) VALUES (%s, %s, %s)",
            params=['Frank', 'frank@example.com', 40]
        )

        # Rollback transaction
        connector.rollback_transaction()

        # Verify record was not inserted
        final_count = len(connector.execute_select("SELECT * FROM test_users"))
        assert final_count == initial_count

        connector.disconnect()

    def test_stream_query_results_from_real_database(
        self, mysql_config, skip_if_no_mysql, test_table_setup
    ):
        """Test streaming query results from real database"""
        connector = MySQLConnector(**mysql_config)
        connector.connect()

        results = []
        for row in connector.execute_query_stream("SELECT * FROM test_users ORDER BY name"):
            results.append(row)
            if len(results) >= 2:  # Just test first 2 rows
                break

        assert len(results) == 2
        assert results[0][1] == 'Alice'

        connector.disconnect()

    def test_get_primary_keys_from_real_database(
        self, mysql_config, skip_if_no_mysql, test_table_setup
    ):
        """Test getting primary key constraints from real database"""
        connector = MySQLConnector(**mysql_config)
        connector.connect()

        pks = connector.get_primary_keys()

        # Check test_users table
        test_users_pk = [pk for pk in pks if pk[0] == 'test_users']
        assert len(test_users_pk) == 1
        assert test_users_pk[0][1] == 'id'

        connector.disconnect()

    def test_get_foreign_keys_from_real_database(
        self, mysql_config, skip_if_no_mysql, test_table_setup
    ):
        """Test getting foreign key constraints from real database"""
        connector = MySQLConnector(**mysql_config)
        connector.connect()

        # Create a table with foreign key for testing
        conn = test_table_setup  # Reuse the connection
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_orders (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                product VARCHAR(100),
                FOREIGN KEY (user_id) REFERENCES test_users(id)
            )
        """)
        conn.commit()
        cursor.close()

        fks = connector.get_foreign_keys()

        # Check test_orders foreign key
        test_orders_fk = [fk for fk in fks if fk['from_table'] == 'test_orders']
        assert len(test_orders_fk) >= 1
        assert test_orders_fk[0]['to_table'] == 'test_users'
        assert test_orders_fk[0]['to_column'] == 'id'

        connector.disconnect()


# ========================================================================
# Mock Integration Tests (No MySQL Required)
# ========================================================================

class TestMySQLConnectorMockIntegration:
    """Integration tests using mocks (no MySQL required)"""

    @patch('src.core.connectors.mysql.pymysql')
    def test_full_workflow_with_mocks(self, mock_pymysql):
        """Test complete workflow using mocked MySQL"""
        # Setup mocks
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_pymysql.connect.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.cursor.return_value.__exit__.return_value = False

        # Mock query results
        mock_cursor.fetchall.side_effect = [
            [('test_users',), ('test_orders',)],  # list_tables
            [('id', 'INT'), ('name', 'VARCHAR')],  # get_table_schema
            [(1, 'Alice'), (2, 'Bob')],  # execute_select
        ]
        mock_cursor.rowcount = 1  # Affected rows for INSERT/UPDATE/DELETE

        # Connect
        connector = MySQLConnector(
            host='localhost',
            port=3306,
            database='testdb',
            user='testuser',
            password='testpass'
        )
        connector.connect()

        assert connector.connected is True

        # List tables
        tables = connector.list_tables()
        assert 'test_users' in tables

        # Get schema
        schema = connector.get_table_schema('test_users')
        assert len(schema) == 2

        # Execute SELECT
        results = connector.execute_select("SELECT * FROM test_users")
        assert len(results) == 2

        # Execute INSERT
        affected = connector.execute_insert(
            "INSERT INTO test_users (name) VALUES (%s)",
            params=['Eve']
        )
        assert affected == 1

        # Disconnect
        connector.disconnect()
        assert connector.connected is False

    @patch('src.core.connectors.mysql.pymysql')
    def test_error_handling_with_mocks(self, mock_pymysql):
        """Test error handling using mocked MySQL"""
        # Setup mock to raise exception
        mock_pymysql.connect.side_effect = Exception("Connection failed")

        connector = MySQLConnector(
            host='localhost',
            port=3306,
            database='testdb',
            user='testuser',
            password='testpass'
        )

        with pytest.raises(Exception, match="Connection failed"):
            connector.connect()

        assert connector.connected is False

    @patch('src.core.connectors.mysql.pymysql')
    def test_connection_pooling_integration(self, mock_pymysql):
        """Test integration with connection pooling"""
        from src.core.database.pool import ConnectionPool

        # Create connection pool
        pool = ConnectionPool(max_connections=5)

        # Mock MySQL connection
        mock_conn = MagicMock()
        mock_pymysql.connect.return_value = mock_conn

        # Acquire connection from pool
        connector = MySQLConnector(
            connection_pool=pool,
            host='localhost',
            port=3306,
            database='testdb',
            user='testuser',
            password='testpass'
        )
        connector.connect()

        assert connector.connected is True

        # Release connection back to pool
        connector.disconnect()

        # Close pool
        pool.close_all()
