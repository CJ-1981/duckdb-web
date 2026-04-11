"""
Unit tests for DuckDB error message mapping function.

Tests the map_duckdb_error_to_user_message function to ensure it properly
translates technical DuckDB errors into user-friendly messages.
"""

import pytest
from src.api.routes.workflows import map_duckdb_error_to_user_message


class TestDuckDBErrorMapping:
    """Test suite for DuckDB error message mapping."""

    def test_invalid_column_error_with_column_name(self):
        """Test mapping of binder error with specific column name."""
        error = Exception('Binder Error: Referenced column "nonexistent_column" not found in FROM clause')
        message = map_duckdb_error_to_user_message(error)

        assert "nonexistent_column" in message
        assert "doesn't exist" in message
        assert "Binder Error" not in message

    def test_invalid_column_error_without_column_name(self):
        """Test mapping of binder error without specific column name."""
        error = Exception('Binder Error: Invalid column')
        message = map_duckdb_error_to_user_message(error)

        assert "column" in message.lower()
        assert "doesn't exist" in message

    def test_parser_error(self):
        """Test mapping of parser error."""
        error = Exception('Parser Error: syntax error at or near "SELECT"')
        message = map_duckdb_error_to_user_message(error)

        assert "SQL syntax error" in message
        assert "please check" in message

    def test_syntax_error(self):
        """Test mapping of syntax error."""
        error = Exception('syntax error: unexpected end of statement')
        message = map_duckdb_error_to_user_message(error)

        assert "SQL syntax error" in message

    def test_catalog_error_table_not_found(self):
        """Test mapping of catalog error for missing table."""
        error = Exception('Catalog Error: Table "missing_table" does not exist')
        message = map_duckdb_error_to_user_message(error)

        assert "missing_table" in message
        assert "doesn't exist" in message

    def test_catalog_error_without_table_name(self):
        """Test mapping of catalog error without table name."""
        error = Exception('Catalog Error: not found')
        message = map_duckdb_error_to_user_message(error)

        assert "table" in message.lower()
        assert "doesn't exist" in message

    def test_type_error(self):
        """Test mapping of type error."""
        error = Exception('Type Error: Cannot cast VARCHAR to INTEGER')
        message = map_duckdb_error_to_user_message(error)

        assert "type mismatch" in message.lower()
        assert "column types" in message

    def test_ambiguous_reference_error(self):
        """Test mapping of ambiguous column reference error."""
        error = Exception('Binder Error: Ambiguous reference to column "id"')
        message = map_duckdb_error_to_user_message(error)

        assert "ambiguous" in message
        assert "specify which table" in message

    def test_unknown_error_fallback(self):
        """Test fallback for unknown error types."""
        error = Exception('Unknown error: some unexpected database issue')
        message = map_duckdb_error_to_user_message(error)

        assert message == str(error)[:200]

    def test_long_error_truncation(self):
        """Test that long errors are truncated in fallback case."""
        long_message = "Error: " + "x" * 300
        error = Exception(long_message)
        message = map_duckdb_error_to_user_message(error)

        assert len(message) <= 200

    def test_case_insensitive_matching(self):
        """Test that error matching is case-insensitive."""
        error = Exception('BINDER ERROR: INVALID COLUMN "test_col"')
        message = map_duckdb_error_to_user_message(error)

        assert "test_col" in message
        assert "doesn't exist" in message