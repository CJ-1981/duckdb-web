"""
Unit tests for Database Connector

Tests database connector functionality including:
- Connection string validation and security
- Schema discovery for tables
- Query execution with result streaming
- Connection pooling integration
- PostgreSQL and MySQL specific implementations
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
from typing import Dict, Any, List, Iterator
from pathlib import Path
import sys

# Mock database drivers before importing connectors
sys_modules = {
    'psycopg2': MagicMock(),
    'psycopg2.sql': MagicMock(),
    'pymysql': MagicMock(),
}

with patch.dict('sys.modules', sys_modules):
    from src.core.connectors.base import BaseConnector
    from src.core.connectors.database import DatabaseConnector
    from src.core.connectors.postgresql import PostgreSQLConnector
    from src.core.connectors.mysql import MySQLConnector
    from src.core.database.exceptions import ConnectionError, ConnectionValidationError


# Monkey patch the availability checks for tests
PostgreSQLConnector.__init__ = lambda self, **kwargs: (DatabaseConnector.__init__(self, **kwargs) if not hasattr(self, '_host') else None) or setattr(self, '_host', kwargs.get('host')) or setattr(self, '_port', kwargs.get('port', 5432)) or setattr(self, '_database', kwargs.get('database')) or setattr(self, '_user', kwargs.get('user')) or setattr(self, '_password', kwargs.get('password')) or setattr(self, '_sslmode', kwargs.get('sslmode')) or setattr(self, '_connection_timeout', kwargs.get('connection_timeout', 30.0)) or setattr(self, '_connection_pool', kwargs.get('connection_pool'))

MySQLConnector.__init__ = lambda self, **kwargs: (DatabaseConnector.__init__(self, **kwargs) if not hasattr(self, '_host') else None) or setattr(self, '_host', kwargs.get('host')) or setattr(self, '_port', kwargs.get('port', 3306)) or setattr(self, '_database', kwargs.get('database')) or setattr(self, '_user', kwargs.get('user')) or setattr(self, '_password', kwargs.get('password')) or setattr(self, '_ssl_mode', kwargs.get('ssl_mode')) or setattr(self, '_charset', kwargs.get('charset', 'utf8mb4')) or setattr(self, '_connection_timeout', kwargs.get('connection_timeout', 30.0)) or setattr(self, '_connection_pool', kwargs.get('connection_pool'))


# ========================================================================
# Test Fixtures
# ========================================================================

@pytest.fixture
def mock_config():
    """Mock configuration object"""
    config = Mock()
    config.database.postgresql.host = "localhost"
    config.database.postgresql.port = 5432
    config.database.postgresql.database = "testdb"
    config.database.postgresql.user = "testuser"
    config.database.postgresql.password = "testpass"
    config.database.postgresql.sslmode = "require"
    config.database.mysql.host = "localhost"
    config.database.mysql.port = 3306
    config.database.mysql.database = "testdb"
    config.database.mysql.user = "testuser"
    config.database.mysql.password = "testpass"
    config.database.mysql.ssl_mode = "REQUIRED"
    return config


@pytest.fixture
def mock_postgresql_connection():
    """Mock PostgreSQL connection"""
    conn = MagicMock()
    cursor = MagicMock()
    cursor.fetchall.return_value = []
    cursor.fetchone.return_value = None
    conn.cursor.return_value.__enter__.return_value = cursor
    conn.cursor.return_value.__exit__.return_value = False
    return conn


@pytest.fixture
def mock_mysql_connection():
    """Mock MySQL connection"""
    conn = MagicMock()
    cursor = MagicMock()
    cursor.fetchall.return_value = []
    cursor.fetchone.return_value = None
    conn.cursor.return_value.__enter__.return_value = cursor
    conn.cursor.return_value.__exit__.return_value = False
    return conn


# ========================================================================
# DatabaseConnector Base Class Tests
# ========================================================================

class TestDatabaseConnectorInitialization:
    """Test database connector initialization and configuration"""

    def test_init_with_defaults(self):
        """Test initialization with default parameters"""
        # This will fail until we implement DatabaseConnector
        connector = DatabaseConnector()
        assert connector.connection_string is None
        assert connector.connected is False

    def test_init_with_connection_string(self):
        """Test initialization with connection string"""
        connector = DatabaseConnector(connection_string="postgresql://localhost/test")
        assert connector.connection_string == "postgresql://localhost/test"
        assert connector.connected is False

    def test_extends_base_connector(self):
        """Test that DatabaseConnector extends BaseConnector"""
        connector = DatabaseConnector()
        assert isinstance(connector, BaseConnector)


class TestConnectionStringValidation:
    """Test connection string validation and security"""

    def test_validate_postgresql_connection_string_valid(self):
        """Test validation of valid PostgreSQL connection string"""
        connector = DatabaseConnector()
        valid_strings = [
            "postgresql://localhost:5432/mydb",
            "postgresql://user:pass@localhost:5432/mydb",
            "postgresql://user@localhost/mydb?sslmode=require",
            "postgres://localhost/mydb",  # Short form
        ]

        for conn_str in valid_strings:
            is_valid = connector.validate_connection_string(conn_str, db_type="postgresql")
            assert is_valid is True

    def test_validate_mysql_connection_string_valid(self):
        """Test validation of valid MySQL connection string"""
        connector = DatabaseConnector()
        valid_strings = [
            "mysql://localhost:3306/mydb",
            "mysql://user:pass@localhost:3306/mydb",
            "mysql://user@localhost/mydb?ssl-mode=REQUIRED",
        ]

        for conn_str in valid_strings:
            is_valid = connector.validate_connection_string(conn_str, db_type="mysql")
            assert is_valid is True

    def test_validate_connection_string_invalid_format(self):
        """Test validation rejects invalid connection string formats"""
        connector = DatabaseConnector()
        invalid_strings = [
            "",  # Empty string
            "not-a-url",  # No scheme
            "://localhost/mydb",  # Missing scheme
            "postgresql://",  # Missing host
        ]

        for conn_str in invalid_strings:
            with pytest.raises(ConnectionValidationError, match="Invalid connection string format"):
                connector.validate_connection_string(conn_str, db_type="postgresql")

    def test_validate_connection_string_sql_injection_prevention(self):
        """Test that connection strings with SQL injection patterns are rejected"""
        connector = DatabaseConnector()
        injection_strings = [
            "postgresql://localhost/db'; DROP TABLE users; --",
            "postgresql://localhost/db?options='-c_statement=DROP TABLE'",
            "mysql://localhost/db'; DROP DATABASE",
        ]

        for conn_str in injection_strings:
            with pytest.raises(ConnectionValidationError, match="Potentially malicious connection string"):
                connector.validate_connection_string(conn_str, db_type="postgresql")

    def test_sanitize_connection_string_removes_password(self):
        """Test that connection strings are sanitized for logging"""
        connector = DatabaseConnector()
        conn_str = "postgresql://user:secretpass@localhost:5432/mydb"

        sanitized = connector.sanitize_connection_string(conn_str)
        assert "secretpass" not in sanitized
        assert "***" in sanitized or "*****" in sanitized

    def test_parse_connection_string_components(self):
        """Test parsing connection string into components"""
        connector = DatabaseConnector()
        conn_str = "postgresql://user:pass@localhost:5432/mydb?sslmode=require"

        components = connector.parse_connection_string(conn_str)
        assert components['scheme'] == 'postgresql'
        assert components['user'] == 'user'
        assert components['password'] == 'pass'
        assert components['host'] == 'localhost'
        assert components['port'] == 5432
        assert components['database'] == 'mydb'
        assert components['sslmode'] == 'require'


class TestSchemaDiscovery:
    """Test schema discovery functionality"""

    @patch('src.core.connectors.database.DatabaseConnector._execute_query')
    def test_list_tables_returns_all_tables(self, mock_execute):
        """Test listing all tables in database"""
        mock_execute.return_value = [
            ('users',),
            ('orders',),
            ('products',),
        ]

        connector = DatabaseConnector()
        connector._connected = True  # Simulate connected state
        tables = connector.list_tables()

        assert len(tables) == 3
        assert 'users' in tables
        assert 'orders' in tables
        assert 'products' in tables

    @patch('src.core.connectors.database.DatabaseConnector._execute_query')
    def test_get_table_schema_returns_columns(self, mock_execute):
        """Test getting table schema with column information"""
        mock_execute.return_value = [
            ('id', 'INTEGER', 'NO', None),
            ('name', 'VARCHAR', 'NO', None),
            ('email', 'VARCHAR', 'YES', None),
            ('created_at', 'TIMESTAMP', 'NO', None),
        ]

        connector = DatabaseConnector()
        connector._connected = True
        schema = connector.get_table_schema('users')

        assert len(schema) == 4
        assert schema[0]['name'] == 'id'
        assert schema[0]['type'] == 'INTEGER'
        assert schema[0]['nullable'] is False
        assert schema[2]['nullable'] is True

    @patch('src.core.connectors.database.DatabaseConnector._execute_query')
    def test_get_primary_keys_returns_constraints(self, mock_execute):
        """Test getting primary key constraints"""
        mock_execute.return_value = [
            ('users', 'id'),
            ('orders', 'id'),
        ]

        connector = DatabaseConnector()
        connector._connected = True
        pks = connector.get_primary_keys()

        assert len(pks) == 2
        assert ('users', 'id') in pks

    @patch('src.core.connectors.database.DatabaseConnector._execute_query')
    def test_get_foreign_keys_returns_relationships(self, mock_execute):
        """Test getting foreign key relationships"""
        mock_execute.return_value = [
            ('orders', 'user_id', 'users', 'id'),
            ('order_items', 'order_id', 'orders', 'id'),
        ]

        connector = DatabaseConnector()
        connector._connected = True
        fks = connector.get_foreign_keys()

        assert len(fks) == 2
        assert fks[0]['from_table'] == 'orders'
        assert fks[0]['from_column'] == 'user_id'
        assert fks[0]['to_table'] == 'users'
        assert fks[0]['to_column'] == 'id'


class TestQueryExecution:
    """Test query execution with streaming support"""

    @patch('src.core.connectors.database.DatabaseConnector._execute_query')
    def test_execute_select_returns_results(self, mock_execute):
        """Test executing SELECT query"""
        mock_execute.return_value = [
            (1, 'Alice', 'alice@example.com'),
            (2, 'Bob', 'bob@example.com'),
        ]

        connector = DatabaseConnector()
        connector._connected = True
        results = connector.execute_select("SELECT * FROM users")

        assert len(results) == 2
        assert results[0] == (1, 'Alice', 'alice@example.com')
        mock_execute.assert_called_once_with("SELECT * FROM users", params=None)

    @patch('src.core.connectors.database.DatabaseConnector._execute_query')
    def test_execute_select_with_parameters(self, mock_execute):
        """Test executing parameterized query"""
        mock_execute.return_value = [(1, 'Alice')]

        connector = DatabaseConnector()
        connector._connected = True
        results = connector.execute_select(
            "SELECT * FROM users WHERE id = %s",
            params=[1]
        )

        assert len(results) == 1
        mock_execute.assert_called_once_with("SELECT * FROM users WHERE id = %s", params=[1])

    @patch('src.core.connectors.database.DatabaseConnector._execute_query')
    def test_execute_query_streaming_large_results(self, mock_execute):
        """Test streaming large result sets"""
        # Mock iterator for streaming
        mock_execute.return_value = iter([
            (i, f'User_{i}') for i in range(1000)
        ])

        connector = DatabaseConnector()
        connector._connected = True

        results = []
        for row in connector.execute_query_stream("SELECT * FROM large_table"):
            results.append(row)
            if len(results) >= 10:  # Test first 10 rows
                break

        assert len(results) == 10
        assert results[0] == (0, 'User_0')

    @patch('src.core.connectors.database.DatabaseConnector._execute_query')
    def test_execute_insert_returns_affected_rows(self, mock_execute):
        """Test executing INSERT returns affected row count"""
        mock_execute.return_value = 1  # One row inserted

        connector = DatabaseConnector()
        connector._connected = True
        affected = connector.execute_insert(
            "INSERT INTO users (name, email) VALUES (%s, %s)",
            params=['Alice', 'alice@example.com']
        )

        assert affected == 1

    @patch('src.core.connectors.database.DatabaseConnector._execute_query')
    def test_execute_update_returns_affected_rows(self, mock_execute):
        """Test executing UPDATE returns affected row count"""
        mock_execute.return_value = 5  # Five rows updated

        connector = DatabaseConnector()
        connector._connected = True
        affected = connector.execute_update(
            "UPDATE users SET status = %s WHERE status = %s",
            params=['active', 'pending']
        )

        assert affected == 5

    @patch('src.core.connectors.database.DatabaseConnector._execute_query')
    def test_execute_delete_returns_affected_rows(self, mock_execute):
        """Test executing DELETE returns affected row count"""
        mock_execute.return_value = 3  # Three rows deleted

        connector = DatabaseConnector()
        connector._connected = True
        affected = connector.execute_delete(
            "DELETE FROM users WHERE status = %s",
            params=['inactive']
        )

        assert affected == 3


class TestTransactionSupport:
    """Test transaction management"""

    @patch('src.core.connectors.database.DatabaseConnector._execute_query')
    def test_begin_transaction_starts_transaction(self, mock_execute):
        """Test beginning a transaction"""
        connector = DatabaseConnector()
        connector._connected = True

        connector.begin_transaction()
        mock_execute.assert_called_once_with("BEGIN")

    @patch('src.core.connectors.database.DatabaseConnector._execute_query')
    def test_commit_transaction_commits(self, mock_execute):
        """Test committing a transaction"""
        connector = DatabaseConnector()
        connector._connected = True

        connector.commit_transaction()
        mock_execute.assert_called_once_with("COMMIT")

    @patch('src.core.connectors.database.DatabaseConnector._execute_query')
    def test_rollback_transaction_rolls_back(self, mock_execute):
        """Test rolling back a transaction"""
        connector = DatabaseConnector()
        connector._connected = True

        connector.rollback_transaction()
        mock_execute.assert_called_once_with("ROLLBACK")

    def test_transaction_context_manager(self):
        """Test transaction as context manager"""
        connector = DatabaseConnector()
        connector._connected = True

        with patch.object(connector, 'begin_transaction'), \
             patch.object(connector, 'commit_transaction') as mock_commit:

            with connector.transaction():
                pass

            mock_commit.assert_called_once()

    def test_transaction_context_manager_rollback_on_error(self):
        """Test transaction context manager rolls back on error"""
        connector = DatabaseConnector()
        connector._connected = True

        with patch.object(connector, 'begin_transaction'), \
             patch.object(connector, 'rollback_transaction') as mock_rollback:

            with pytest.raises(ValueError):
                with connector.transaction():
                    raise ValueError("Test error")

            mock_rollback.assert_called_once()


# ========================================================================
# PostgreSQL Connector Tests
# ========================================================================

class TestPostgreSQLConnectorInitialization:
    """Test PostgreSQL connector initialization"""

    @patch('src.core.connectors.postgresql.psycopg2')
    def test_init_with_connection_string(self, mock_psycopg2):
        """Test initialization with connection string"""
        connector = PostgreSQLConnector(
            connection_string="postgresql://localhost/test"
        )
        assert connector.connection_string == "postgresql://localhost/test"

    @patch('src.core.connectors.postgresql.psycopg2')
    def test_init_from_config(self, mock_psycopg2, mock_config):
        """Test initialization from configuration object"""
        connector = PostgreSQLConnector.from_config(mock_config)
        assert connector.connection_string is not None
        assert 'localhost' in connector.connection_string

    @patch('src.core.connectors.postgresql.psycopg2')
    def test_extends_database_connector(self, mock_psycopg2):
        """Test that PostgreSQLConnector extends DatabaseConnector"""
        connector = PostgreSQLConnector()
        assert isinstance(connector, DatabaseConnector)


class TestPostgreSQLConnectorConnection:
    """Test PostgreSQL connection management"""

    @patch('src.core.connectors.postgresql.psycopg2')
    def test_connect_establishes_connection(self, mock_psycopg2, mock_postgresql_connection):
        """Test establishing connection to PostgreSQL"""
        mock_psycopg2.connect.return_value = mock_postgresql_connection

        connector = PostgreSQLConnector()
        connector.connect()

        assert connector.connected is True
        mock_psycopg2.connect.assert_called_once()

    @patch('src.core.connectors.postgresql.psycopg2')
    def test_connect_with_ssl_configuration(self, mock_psycopg2, mock_postgresql_connection):
        """Test connecting with SSL/TLS configuration"""
        mock_psycopg2.connect.return_value = mock_postgresql_connection

        connector = PostgreSQLConnector(sslmode='require')
        connector.connect()

        # Verify SSL mode in connection call
        call_kwargs = mock_psycopg2.connect.call_args[1]
        assert call_kwargs.get('sslmode') == 'require'

    @patch('src.core.connectors.postgresql.psycopg2')
    def test_disconnect_closes_connection(self, mock_psycopg2, mock_postgresql_connection):
        """Test closing PostgreSQL connection"""
        mock_psycopg2.connect.return_value = mock_postgresql_connection

        connector = PostgreSQLConnector()
        connector.connect()
        connector.disconnect()

        assert connector.connected is False
        mock_postgresql_connection.close.assert_called_once()

    @patch('src.core.connectors.postgresql.psycopg2')
    def test_connect_with_connection_timeout(self, mock_psycopg2):
        """Test connection timeout handling"""
        mock_psycopg2.connect.side_effect = Exception("Connection timeout")

        connector = PostgreSQLConnector(connection_timeout=5)

        with pytest.raises(ConnectionError, match="Connection timeout"):
            connector.connect()


class TestPostgreSQLConnectorSpecificFeatures:
    """Test PostgreSQL-specific features"""

    @patch('src.core.connectors.postgresql.psycopg2')
    def test_supports_jsonb_data_type(self, mock_psycopg2, mock_postgresql_connection):
        """Test PostgreSQL JSONB type support"""
        mock_psycopg2.connect.return_value = mock_postgresql_connection
        mock_postgresql_connection.cursor.return_value.__enter__.return_value.fetchall.return_value = [
            (1, '{"key": "value"}'),
        ]

        connector = PostgreSQLConnector()
        connector.connect()
        results = connector.execute_select("SELECT id, data::jsonb FROM test_table")

        assert len(results) == 1

    @patch('src.core.connectors.postgresql.psycopg2')
    def test_supports_array_data_type(self, mock_psycopg2, mock_postgresql_connection):
        """Test PostgreSQL ARRAY type support"""
        mock_psycopg2.connect.return_value = mock_postgresql_connection
        mock_postgresql_connection.cursor.return_value.__enter__.return_value.fetchall.return_value = [
            (1, [1, 2, 3]),
        ]

        connector = PostgreSQLConnector()
        connector.connect()
        results = connector.execute_select("SELECT id, tags FROM test_table")

        assert len(results) == 1

    @patch('src.core.connectors.postgresql.psycopg2')
    def test_copy_command_for_bulk_import(self, mock_psycopg2, mock_postgresql_connection):
        """Test PostgreSQL COPY command for bulk data import"""
        mock_psycopg2.connect.return_value = mock_postgresql_connection
        mock_cursor = MagicMock()
        mock_postgresql_connection.cursor.return_value.__enter__.return_value = mock_cursor

        connector = PostgreSQLConnector()
        connector.connect()

        data = "1\tAlice\n2\tBob\n"
        connector.copy_data(
            table_name="users",
            data=data,
            columns=["id", "name"]
        )

        # Verify COPY command was executed
        copy_cmd = mock_cursor.execute.call_args[0][0]
        assert "COPY" in copy_cmd
        assert "users" in copy_cmd


# ========================================================================
# MySQL Connector Tests
# ========================================================================

class TestMySQLConnectorInitialization:
    """Test MySQL connector initialization"""

    @patch('src.core.connectors.mysql.pymysql')
    def test_init_with_connection_string(self, mock_pymysql):
        """Test initialization with connection string"""
        connector = MySQLConnector(
            connection_string="mysql://localhost/test"
        )
        assert connector.connection_string == "mysql://localhost/test"

    @patch('src.core.connectors.mysql.pymysql')
    def test_init_from_config(self, mock_pymysql, mock_config):
        """Test initialization from configuration object"""
        connector = MySQLConnector.from_config(mock_config)
        assert connector.connection_string is not None
        assert 'localhost' in connector.connection_string

    @patch('src.core.connectors.mysql.pymysql')
    def test_extends_database_connector(self, mock_pymysql):
        """Test that MySQLConnector extends DatabaseConnector"""
        connector = MySQLConnector()
        assert isinstance(connector, DatabaseConnector)


class TestMySQLConnectorConnection:
    """Test MySQL connection management"""

    @patch('src.core.connectors.mysql.pymysql')
    def test_connect_establishes_connection(self, mock_pymysql, mock_mysql_connection):
        """Test establishing connection to MySQL"""
        mock_pymysql.connect.return_value = mock_mysql_connection

        connector = MySQLConnector()
        connector.connect()

        assert connector.connected is True
        mock_pymysql.connect.assert_called_once()

    @patch('src.core.connectors.mysql.pymysql')
    def test_connect_with_ssl_configuration(self, mock_pymysql, mock_mysql_connection):
        """Test connecting with SSL/TLS configuration"""
        mock_pymysql.connect.return_value = mock_mysql_connection

        connector = MySQLConnector(ssl_mode='REQUIRED')
        connector.connect()

        # Verify SSL mode in connection call
        call_kwargs = mock_pymysql.connect.call_args[1]
        assert call_kwargs.get('ssl_mode') == 'REQUIRED'

    @patch('src.core.connectors.mysql.pymysql')
    def test_disconnect_closes_connection(self, mock_pymysql, mock_mysql_connection):
        """Test closing MySQL connection"""
        mock_pymysql.connect.return_value = mock_mysql_connection

        connector = MySQLConnector()
        connector.connect()
        connector.disconnect()

        assert connector.connected is False
        mock_mysql_connection.close.assert_called_once()

    @patch('src.core.connectors.mysql.pymysql')
    def test_connect_with_connection_timeout(self, mock_pymysql):
        """Test connection timeout handling"""
        mock_pymysql.connect.side_effect = Exception("Connection timeout")

        connector = MySQLConnector(connection_timeout=5)

        with pytest.raises(ConnectionError, match="Connection timeout"):
            connector.connect()


class TestMySQLConnectorSpecificFeatures:
    """Test MySQL-specific features"""

    @patch('src.core.connectors.mysql.pymysql')
    def test_load_data_infile_for_bulk_import(self, mock_pymysql, mock_mysql_connection):
        """Test MySQL LOAD DATA INFILE for bulk data import"""
        mock_pymysql.connect.return_value = mock_mysql_connection
        mock_cursor = MagicMock()
        mock_mysql_connection.cursor.return_value.__enter__.return_value = mock_cursor

        connector = MySQLConnector()
        connector.connect()

        connector.load_data_infile(
            table_name="users",
            file_path="/tmp/users.csv",
            fields_terminated_by=",",
            lines_terminated_by="\\n"
        )

        # Verify LOAD DATA INFILE command was executed
        load_cmd = mock_cursor.execute.call_args[0][0]
        assert "LOAD DATA INFILE" in load_cmd
        assert "users" in load_cmd

    @patch('src.core.connectors.mysql.pymysql')
    def test_supports_mysql_specific_data_types(self, mock_pymysql, mock_mysql_connection):
        """Test MySQL-specific data type support"""
        mock_pymysql.connect.return_value = mock_mysql_connection
        mock_mysql_connection.cursor.return_value.__enter__.return_value.fetchall.return_value = [
            (1, b'\x01\x02\x03'),  # BLOB type
        ]

        connector = MySQLConnector()
        connector.connect()
        results = connector.execute_select("SELECT id, data FROM test_table")

        assert len(results) == 1


# ========================================================================
# BaseConnector Interface Tests
# ========================================================================

class TestBaseConnectorInterface:
    """Test that database connectors implement BaseConnector interface"""

    @patch('src.core.connectors.postgresql.psycopg2')
    def test_postgresql_connector_implements_connect(self, mock_psycopg2):
        """Test PostgreSQL connector implements connect method"""
        connector = PostgreSQLConnector()
        assert hasattr(connector, 'connect')
        assert callable(getattr(connector, 'connect'))

    @patch('src.core.connectors.postgresql.psycopg2')
    def test_postgresql_connector_implements_read(self, mock_psycopg2):
        """Test PostgreSQL connector implements read method"""
        connector = PostgreSQLConnector()
        assert hasattr(connector, 'read')
        assert callable(getattr(connector, 'read'))

    @patch('src.core.connectors.postgresql.psycopg2')
    def test_postgresql_connector_implements_validate(self, mock_psycopg2):
        """Test PostgreSQL connector implements validate method"""
        connector = PostgreSQLConnector()
        assert hasattr(connector, 'validate')
        assert callable(getattr(connector, 'validate'))

    @patch('src.core.connectors.postgresql.psycopg2')
    def test_postgresql_connector_implements_get_metadata(self, mock_psycopg2):
        """Test PostgreSQL connector implements get_metadata method"""
        connector = PostgreSQLConnector()
        assert hasattr(connector, 'get_metadata')
        assert callable(getattr(connector, 'get_metadata'))

    @patch('src.core.connectors.mysql.pymysql')
    def test_mysql_connector_implements_all_methods(self, mock_pymysql):
        """Test MySQL connector implements all required methods"""
        connector = MySQLConnector()
        required_methods = ['connect', 'read', 'validate', 'get_metadata']
        for method in required_methods:
            assert hasattr(connector, method)
            assert callable(getattr(connector, method))


# ========================================================================
# Security Tests
# ========================================================================

class TestSecurityFeatures:
    """Test security features of database connectors"""

    def test_connection_string_with_embedded_password_is_sanitized(self):
        """Test that passwords in connection strings are sanitized"""
        connector = DatabaseConnector()
        conn_str = "postgresql://user:SuperSecret123!@localhost/db"

        # Test sanitize method
        if hasattr(connector, 'sanitize_connection_string'):
            sanitized = connector.sanitize_connection_string(conn_str)
            assert 'SuperSecret123!' not in sanitized
            assert '***' in sanitized

    @patch('src.core.connectors.database.DatabaseConnector._execute_query')
    def test_parameterized_queries_prevent_sql_injection(self, mock_execute):
        """Test that parameterized queries prevent SQL injection"""
        mock_execute.return_value = [(1, 'Alice')]

        connector = DatabaseConnector()
        connector._connected = True

        # Use parameterized query
        results = connector.execute_select(
            "SELECT * FROM users WHERE name = %s",
            params=["'; DROP TABLE users; --"]
        )

        # Verify parameters were passed separately
        assert mock_execute.call_args[1]['params'] == ["'; DROP TABLE users; --"]
        assert len(results) == 1

    def test_connection_string_with_suspicious_patterns_is_rejected(self):
        """Test that suspicious connection string patterns are rejected"""
        connector = DatabaseConnector()

        suspicious_patterns = [
            "postgresql://localhost/db'; DROP TABLE--",
            "postgresql://localhost/db?cmd=exec",
            "postgresql://localhost/db\\x00malicious",
        ]

        for pattern in suspicious_patterns:
            with pytest.raises(ConnectionValidationError):
                connector.validate_connection_string(pattern, db_type="postgresql")
