"""
Workflow Routes

FastAPI routes for workflow CRUD operations.
"""

from typing import Optional, List, Dict, Any
import os
import uuid
import json
import logging
import time
import re
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
import duckdb
import math
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table as RLTable, TableStyle, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

logger = logging.getLogger(__name__)

# Pre-compiled regex patterns for SQL injection prevention
# Compiled at module load for better performance (avoids recompilation on every validation)
# IMPORTANT: All patterns use re.IGNORECASE because SQL is case-insensitive
SQL_INJECTION_PATTERNS = [
    re.compile(r';', re.IGNORECASE),           # Statement separator
    re.compile(r'--', re.IGNORECASE),          # SQL comment
    re.compile(r'/\*', re.IGNORECASE),         # SQL comment start
    re.compile(r'\*/', re.IGNORECASE),         # SQL comment end
    re.compile(r'\bDROP\b', re.IGNORECASE),     # DROP statement
    re.compile(r'\bDELETE\b', re.IGNORECASE),   # DELETE statement
    re.compile(r'\bINSERT\b', re.IGNORECASE),   # INSERT statement
    re.compile(r'\bUPDATE\b', re.IGNORECASE),   # UPDATE statement
    re.compile(r'\bEXEC\b', re.IGNORECASE),     # EXEC statement
    re.compile(r'\bEXECUTE\b', re.IGNORECASE),  # EXECUTE statement
    re.compile(r'\bGRANT\b', re.IGNORECASE),    # GRANT statement
    re.compile(r'\bREVOKE\b', re.IGNORECASE),   # REVOKE statement
    re.compile(r'\bALTER\b', re.IGNORECASE),    # ALTER statement
    re.compile(r'\bCREATE\b', re.IGNORECASE),   # CREATE statement
    re.compile(r'\bTRUNCATE\b', re.IGNORECASE), # TRUNCATE statement
]

EXPRESSION_PATTERNS = [
    re.compile(r'\s*=\s*', re.IGNORECASE),     # Equals operator
    re.compile(r'\s+OR\s+', re.IGNORECASE),     # OR operator
    re.compile(r'\s+AND\s+', re.IGNORECASE),    # AND operator
    re.compile(r'\s*\+\s*', re.IGNORECASE),     # Addition operator
    re.compile(r'\s*-\s*', re.IGNORECASE),     # Subtraction operator
    re.compile(r'\s*\*\s*', re.IGNORECASE),     # Multiplication operator
    re.compile(r'\s*/\s*', re.IGNORECASE),     # Division operator
    re.compile(r'\(\s*SELECT\s+', re.IGNORECASE), # Subquery
    re.compile(r'\bCASE\s+WHEN', re.IGNORECASE), # CASE expression
    re.compile(r';', re.IGNORECASE),            # Statement separator
    re.compile(r'--', re.IGNORECASE),           # SQL comment
    re.compile(r'/\*', re.IGNORECASE),          # SQL comment
    re.compile(r'\|\|', re.IGNORECASE),         # String concatenation (PostgreSQL)
    re.compile(r'^\s*\(', re.IGNORECASE),       # Starting parenthesis (expression)
]

# Additional validation patterns for query parameters
PARAMETER_NAME_PATTERN = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_-]*$')  # Valid parameter names (allowing hyphens for node IDs)
TABLE_NAME_PATTERN = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_-]*(\.[a-zA-Z_][a-zA-Z0-9_-]*)?$')  # Valid table names

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.connectors.csv import clean_invisible_unicode

from src.api.auth.dependencies import get_current_user, get_db
from src.api.auth.decorators import require_permission
from src.api.models.user import User
from src.api.schemas.workflow import (
    WorkflowCreate,
    WorkflowUpdate,
    WorkflowResponse,
    WorkflowListResponse
)
from src.api.services.workflow import WorkflowService
from src.api.services.schema_analyzer import SchemaAnalyzerService
from src.core.connectors.csv import CSVConnector
import time
_CSV_SCHEMA_CACHE = {}
from src.core.connectors.csv import CSVConnector


router = APIRouter(prefix="/api/v1/workflows", tags=["Workflows"])

# Global State for Incremental Caching
# node_id -> { "hash": str, "table_name": str, "timestamp": float }
_NODE_CACHE: Dict[str, Dict[str, Any]] = {}
_GLOBAL_CONN: Optional[duckdb.DuckDBPyConnection] = None

# CSV Schema Cache for type inference
# file_path -> { "schema": Dict[str, str], "timestamp": float }
_CSV_SCHEMA_CACHE: Dict[str, Dict[str, Any]] = {}

# SQL Result Cache for query preview results
# cache_key -> { "result": Dict, "timestamp": float }
_SQL_RESULT_CACHE: Dict[str, Dict[str, Any]] = {}
# Maximum cache size to prevent unbounded growth
_MAX_SQL_RESULT_CACHE_SIZE = 100

def get_connection():
    global _GLOBAL_CONN
    if _GLOBAL_CONN is None:
        _GLOBAL_CONN = duckdb.connect(database=':memory:')
    return _GLOBAL_CONN

def get_or_infer_csv_schema(file_path: str) -> Dict[str, Any]:
    """
    Get cached CSV schema or infer from file

    Args:
        file_path: Path to CSV file

    Returns:
        Dictionary containing:
            - "schema": Dictionary mapping column names to inferred DuckDB types
            - "encoding": Detected file encoding
            - "delimiter": Detected delimiter
    """
    # Check cache first
    if file_path in _CSV_SCHEMA_CACHE:
        cache_entry = _CSV_SCHEMA_CACHE[file_path]
        logger.info(f">>> [CSV SCHEMA] Using cached schema for {file_path}")
        return cache_entry

    # Determine sample size based on file size
    import os
    file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
    sample_rows = 1000 if file_size > 100 * 1024 * 1024 else None  # 100MB threshold

    if sample_rows:
        logger.info(f">>> [CSV SCHEMA] Inferring schema from {file_path} (sampling {sample_rows} rows, file size: {file_size / (1024*1024):.1f}MB)")
    else:
        logger.info(f">>> [CSV SCHEMA] Inferring schema from {file_path} (full scan, file size: {file_size / (1024*1024):.1f}MB)")

    # Infer schema
    try:
        connector = CSVConnector()
        schema = connector.infer_schema(file_path, max_rows=sample_rows)
        encoding = connector.encoding
        delimiter = connector.delimiter

        # Cache the result
        entry = {
            "schema": schema,
            "encoding": encoding,
            "delimiter": delimiter,
            "timestamp": time.time()
        }
        _CSV_SCHEMA_CACHE[file_path] = entry

        logger.info(f">>> [CSV SCHEMA] Detected {len(schema)} columns with encoding {encoding}, delim '{delimiter}'")
        return entry

    except Exception as e:
        logger.error(f">>> [CSV SCHEMA] Failed to infer schema: {str(e)}")
        # Return empty schema on failure (fallback to ALL_VARCHAR behavior)
        logger.warning(f">>> [CSV SCHEMA] Schema inference failed for {file_path}, using ALL_VARCHAR fallback")
        return {"schema": {}, "encoding": "utf-8", "delimiter": ","}

def _generate_sql_cache_key(sql: str, input_schemas: Dict[str, Dict[str, str]]) -> str:
    """
    Generate a cache key for SQL query results.

    The key incorporates the SQL query and schema fingerprints of input tables
    to ensure cache invalidation when input data changes.

    Args:
        sql: The SQL query string
        input_schemas: Dictionary mapping input table names to their column schemas

    Returns:
        A hash-based cache key string
    """
    import hashlib
    import json

    # Create a deterministic string from SQL and input schemas
    # Normalize SQL whitespace for consistency
    normalized_sql = " ".join(sql.split())

    # Create schema fingerprint (column names and types)
    schema_fingerprint = json.dumps(
        {table: sorted(schema.items()) for table, schema in input_schemas.items()},
        sort_keys=True
    )

    # Combine SQL and schema for hash
    combined = f"{normalized_sql}|{schema_fingerprint}"
    cache_key = hashlib.sha256(combined.encode()).hexdigest()[:32]

    return cache_key

def _evict_old_sql_cache_entries():
    """
    Evict old entries from SQL result cache using LRU policy.

    Removes the oldest entries when cache size exceeds maximum.
    """
    if len(_SQL_RESULT_CACHE) <= _MAX_SQL_RESULT_CACHE_SIZE:
        return

    # Sort entries by timestamp and remove oldest
    sorted_entries = sorted(
        _SQL_RESULT_CACHE.items(),
        key=lambda x: x[1]["timestamp"]
    )

    # Calculate number of entries to remove
    num_to_remove = len(_SQL_RESULT_CACHE) - _MAX_SQL_RESULT_CACHE_SIZE + 10  # Remove extra for buffer

    for i in range(num_to_remove):
        cache_key, _ = sorted_entries[i]
        del _SQL_RESULT_CACHE[cache_key]
        logger.info(f">>> [SQL CACHE] Evicted old cache entry: {cache_key}")

def _get_cached_sql_result(cache_key: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve cached SQL query result if available.

    Args:
        cache_key: The cache key generated by _generate_sql_cache_key

    Returns:
        Cached result dictionary or None if not found/expired
    """
    if cache_key not in _SQL_RESULT_CACHE:
        return None

    cache_entry = _SQL_RESULT_CACHE[cache_key]

    # Cache entries expire after 30 minutes
    cache_ttl = 30 * 60  # 30 minutes in seconds
    if time.time() - cache_entry["timestamp"] > cache_ttl:
        del _SQL_RESULT_CACHE[cache_key]
        logger.info(f">>> [SQL CACHE] Cache entry expired: {cache_key}")
        return None

    logger.info(f">>> [SQL CACHE] Cache hit for key: {cache_key}")
    return cache_entry["result"]

def _cache_sql_result(cache_key: str, result: Dict[str, Any]):
    """
    Store SQL query result in cache.

    Args:
        cache_key: The cache key generated by _generate_sql_cache_key
        result: The query result to cache
    """
    # Evict old entries if cache is full
    _evict_old_sql_cache_entries()

    _SQL_RESULT_CACHE[cache_key] = {
        "result": result,
        "timestamp": time.time()
    }
    logger.info(f">>> [SQL CACHE] Cached result for key: {cache_key} (cache size: {len(_SQL_RESULT_CACHE)})")

def _invalidate_sql_cache_for_table(table_name: str):
    """
    Invalidate all SQL cache entries that reference a specific table.

    This should be called when input data changes to ensure stale results are not used.

    Args:
        table_name: Name of the table whose data has changed
    """
    keys_to_remove = []

    # Note: This is a simple implementation. In production, you'd want to track
    # which cache entries depend on which tables for more efficient invalidation.
    # For now, we clear the entire cache when any data changes.
    _SQL_RESULT_CACHE.clear()
    logger.info(f">>> [SQL CACHE] Cleared entire cache due to table change: {table_name}")

def _build_regex_clean_expression(col_ref: str) -> str:
    """
    Build DuckDB regexp_replace expression to clean Korean number format characters.

    Removes commas, currency symbols (₩, $, ¥, €, £) in a single regex pass.
    Handles empty strings by returning NULL.

    Args:
        col_ref: Column reference to clean

    Returns:
        DuckDB SQL expression with regexp_replace
    """
    # Remove all Korean number format characters in one pass: commas and currency symbols
    # Use 'g' flag for global replacement (all occurrences, not just first)
    # Handle empty strings: NULLIF converts empty string to NULL before TRY_CAST
    return f"NULLIF(REGEXP_REPLACE({col_ref}, '[,₩$¥€£]', '', 'g'), '')"

def build_cast_expressions(schema: Dict[str, str], table_alias: str = "", actual_cols: List[str] = None) -> List[str]:
    """
    Build SQL CAST expressions for detected column types

    Args:
        schema: Dictionary mapping cleaned column names to DuckDB types
        table_alias: Optional table alias for column references
        actual_cols: Optional list of raw column names from the source table

    Returns:
        List of SQL expressions for SELECT clause
    """
    if not schema:
        return ["*"]

    # If actual_cols is provided, create a map from cleaned name to raw name
    # This handles cases where DuckDB and Python inference differ slightly in header cleaning
    name_map = {}
    if actual_cols:
        for raw in actual_cols:
            clean = clean_invisible_unicode(raw)
            name_map[clean] = raw

    cast_expressions = []
    for col_name, col_type in schema.items():
        # Use raw name if found in map, otherwise use the col_name from schema
        raw_name = name_map.get(col_name, col_name)
        
        quoted_raw = quote_identifier(raw_name)
        quoted_clean = quote_identifier(col_name)
        
        col_ref = f"{table_alias}.{quoted_raw}" if table_alias else quoted_raw

        if col_type == 'INTEGER':
            # Clean Korean format (commas, currency) and cast to INTEGER
            # Use COALESCE to handle NULL values after cleaning
            clean_expr = _build_regex_clean_expression(col_ref)
            cast_expressions.append(
                f"COALESCE(TRY_CAST({clean_expr} AS INTEGER), NULL::INTEGER) AS {quoted_clean}"
            )
        elif col_type == 'FLOAT':
            # Clean Korean format and cast to DOUBLE (FLOAT in DuckDB)
            # Use COALESCE to handle NULL values after cleaning
            clean_expr = _build_regex_clean_expression(col_ref)
            cast_expressions.append(
                f"COALESCE(TRY_CAST({clean_expr} AS DOUBLE), NULL::DOUBLE) AS {quoted_clean}"
            )
        elif col_type == 'DATE':
            # Cast to DATE
            cast_expressions.append(
                f"TRY_CAST({col_ref} AS DATE) AS {quoted_clean}"
            )
        elif col_type == 'BOOLEAN':
            # Cast to BOOLEAN
            cast_expressions.append(
                f"CASE WHEN LOWER({col_ref}) IN ('true', '1', 'yes') THEN TRUE "
                f"WHEN LOWER({col_ref}) IN ('false', '0', 'no') THEN FALSE "
                f"ELSE NULL END AS {quoted_clean}"
            )
        else:
            # VARCHAR - ensure it's trimmed and cast to VARCHAR, then aliased to cleaned name
            # Use NULLIF to convert empty strings to NULL for proper NULL counting
            cast_expressions.append(f"NULLIF(TRIM(CAST({col_ref} AS VARCHAR)), '') AS {quoted_clean}")

    return cast_expressions

def quote_identifier(name: str) -> str:
    """Quote a SQL identifier and escape internal double quotes for DuckDB/Standard SQL.

    Strips invisible Unicode characters (BOM, zero-width characters, etc.) that can cause SQL errors.
    Uses shared utility function clean_invisible_unicode() to avoid code duplication.
    """
    if not name:
        return '""'

    # Use shared utility to strip invisible Unicode characters
    cleaned = clean_invisible_unicode(name)

    return f'"{cleaned.replace("\"", "\"\"")}"'


def fix_replace_for_numeric_columns(sql: str, schema: Dict[str, str]) -> str:
    """
    Fix REPLACE() function calls for numeric columns

    When columns are automatically detected as numeric (INTEGER, FLOAT, DOUBLE),
    but the user's SQL still contains REPLACE(column, ',', '') for Korean format cleaning,
    we need to cast the column to VARCHAR first since REPLACE() only accepts VARCHAR.

    Args:
        sql: User's SQL query
        schema: Column name to type mapping from schema inference

    Returns:
        SQL with REPLACE calls fixed for numeric columns
    """
    import re

    # Pattern to match REPLACE function calls with column names
    # Matches: REPLACE(column_name, search, replace) or REPLACE("column name", search, replace)
    # We need to find the first argument (column name) and check if it's numeric
    replace_pattern = r'REPLACE\s*\(\s*"?([a-zA-Z0-9_\uAC00-\uD7A3\u4E00-\u9FFF\u3040-\u309F\u0400-\u04FF]+)"?\s*,'

    def fix_replace_match(match):
        """Fix a single REPLACE call if the column is numeric"""
        column_name = match.group(1)

        # Check if this column exists in schema and is numeric
        if column_name in schema:
            col_type = schema[column_name]
            # Check if numeric type
            if any(t in col_type.upper() for t in ['INTEGER', 'FLOAT', 'DOUBLE', 'DECIMAL', 'NUMERIC', 'BIGINT', 'REAL', 'HUGEINT']):
                # Wrap column in CAST to VARCHAR
                quoted_col = quote_identifier(column_name)
                # Replace just the column name part
                return f'REPLACE(CAST({quoted_col} AS VARCHAR),'

        return match.group(0)

    # Apply the fix
    fixed_sql = re.sub(replace_pattern, fix_replace_match, sql)

    return fixed_sql


def map_duckdb_error_to_user_message(error: Exception) -> str:
    """
    Translate DuckDB errors to user-friendly messages.

    Converts technical DuckDB error messages into clear, actionable guidance
    for non-technical users. Extracts specific details like column names and
    provides contextual help.

    Args:
        error: The DuckDB exception to translate

    Returns:
        A user-friendly error message
    """
    import re
    error_str = str(error).lower()
    error_original = str(error)

    # Ambiguous reference errors (check before binder error)
    if "ambiguous" in error_str:
        return "A column name is ambiguous - specify which table it comes from"

    # Parser/Syntax errors
    if "parser error" in error_str or "syntax error" in error_str:
        return "SQL syntax error - please check your SQL statement"

    # Type errors
    if "type error" in error_str or "type mismatch" in error_str:
        return "Data type mismatch - check that your column types match the operation"

    # Binder Error: Referenced column not found
    if "binder error" in error_str:
        # Try to extract column name from error message
        col_match = re.search(r'"([^"]+)"', error_original)
        if col_match and ("referenced column" in error_str or "column" in error_str):
            return f"The column '{col_match.group(1)}' doesn't exist in your data"
        if "column" in error_str:
            return "A column from your SQL doesn't exist in the data"
        return "Table or column reference error - please check your SQL"

    # Catalog errors (table not found or does not exist)
    if "catalog error" in error_str:
        # Try to extract table name from error message
        table_match = re.search(r'table "([^"]+)"|table with name ([^\s]+)', error_original, re.IGNORECASE)
        if table_match:
            table_name = table_match.group(1) or table_match.group(2)
            return f"The table '{table_name}' doesn't exist"
        if "not found" in error_str or "does not exist" in error_str:
            return "A referenced table doesn't exist"
        return "Table reference error - please check table names"

    # Fallback: truncated original error
    return error_original[:200]


def validate_sql_fragment(conn: duckdb.DuckDBPyConnection, sql_fragment: str, fragment_type: str = "expression") -> None:
    """
    Validate a SQL fragment to prevent SQL injection.

    This function validates SQL syntax and prevents malicious SQL injection.
    For WHEN clauses, it uses pattern-based validation instead of EXPLAIN
    to avoid column binding errors.

    Args:
        conn: DuckDB connection
        sql_fragment: SQL fragment to validate (WHERE clause, expression, etc.)
        fragment_type: Type of fragment for error messages (WHERE, expression, WHEN, etc.)

    Raises:
        HTTPException: If SQL fragment is invalid or potentially malicious
    """
    if not sql_fragment or not sql_fragment.strip():
        return

    # For WHEN clauses, use pattern-based validation to avoid column binding issues
    if fragment_type == "WHEN":
        # Use pre-compiled regex patterns for better performance
        for pattern in SQL_INJECTION_PATTERNS:
            if pattern.search(sql_fragment):
                logger.error(f"SQL validation failed for {fragment_type}: dangerous pattern '{pattern}' detected")
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid {fragment_type} clause: potentially dangerous SQL detected"
                )
        # WHEN clause validation passed
        return

    # For other fragment types, use EXPLAIN validation
    try:
        # Use EXPLAIN to validate syntax without executing
        # We wrap the fragment in a SELECT with dummy columns to prevent binding errors
        if fragment_type == "WHERE":
            test_sql = f"EXPLAIN SELECT 1 AS dummy WHERE FALSE AND ({sql_fragment})"
        elif fragment_type == "expression":
            test_sql = f"EXPLAIN SELECT {sql_fragment} AS validation_column, 1 AS dummy WHERE FALSE"
        else:
            test_sql = f"EXPLAIN SELECT {sql_fragment}, 1 AS dummy WHERE FALSE"

        conn.execute(test_sql)
    except Exception as e:
        logger.error(f"SQL validation failed for {fragment_type}: {sql_fragment[:100]}... Error: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid {fragment_type} clause: {str(e)}"
        )


def is_simple_identifier(value: str) -> bool:
    """
    Check if a value is a simple SQL identifier (column name), not an expression.

    This prevents SQL injection by checking for dangerous patterns like:
    - Operators (=, +, -, *, /, OR, AND, etc.)
    - Function calls (parentheses)
    - Subqueries (SELECT, FROM, WHERE, etc.)
    - Semicolons (statement separators)

    Valid identifiers can contain letters, numbers, spaces, underscores, and Unicode characters.
    They will be properly quoted by quote_identifier() which handles escaping.

    Args:
        value: Value to check

    Returns:
        True if value appears to be a simple identifier, False if it looks like an expression
    """
    if not value:
        return True

    # Remove surrounding quotes
    cleaned = value.strip().strip('"').strip('`').strip('[]')

    # Check for dangerous SQL patterns that indicate expressions
    # Use pre-compiled regex patterns for better performance
    for pattern in EXPRESSION_PATTERNS:
        if pattern.search(cleaned):
            return False

    # Allow alphanumeric, spaces, underscores, and Unicode characters (Korean, Chinese, etc.)
    # quote_identifier() will properly handle escaping
    return True


def validate_table_name(table_name: str) -> bool:
    """
    Validate table name to prevent SQL injection via table names.

    Checks that the table name contains only valid characters (letters, numbers,
    underscores, dots for schema.table) and doesn't contain dangerous patterns.

    Args:
        table_name: Table name to validate

    Returns:
        True if table name is safe, False otherwise

    Raises:
        HTTPException: If table name contains invalid characters or patterns
    """
    if not table_name or not table_name.strip():
        raise HTTPException(
            status_code=400,
            detail="Table name cannot be empty"
        )

    # Use pre-compiled pattern for validation
    if not TABLE_NAME_PATTERN.match(table_name.strip()):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid table name '{table_name}'. Table names must start with a letter or underscore, and contain only letters, numbers, underscores, and dots (for schema.table format)."
        )

    # Check for SQL injection patterns
    for pattern in SQL_INJECTION_PATTERNS:
        if pattern.search(table_name):
            raise HTTPException(
                status_code=400,
                detail=f"Table name contains potentially dangerous pattern: {table_name}"
            )

    return True


def validate_column_name(column_name: str) -> bool:
    """
    Validate column name to prevent SQL injection via column names.

    Similar to table name validation but allows spaces (for quoted identifiers).

    Args:
        column_name: Column name to validate

    Returns:
        True if column name is safe, False otherwise

    Raises:
        HTTPException: If column name contains invalid patterns
    """
    if not column_name or not column_name.strip():
        raise HTTPException(
            status_code=400,
            detail="Column name cannot be empty"
        )

    # Check for SQL injection patterns (but allow spaces which will be handled by quote_identifier)
    for pattern in SQL_INJECTION_PATTERNS:
        if pattern.search(column_name):
            raise HTTPException(
                status_code=400,
                detail=f"Column name contains potentially dangerous pattern: {column_name}"
            )

    return True


def validate_sql_query_length(sql: str, max_length: int = 100000) -> None:
    """
    Validate SQL query length to prevent DoS via excessively long queries.

    Args:
        sql: SQL query to validate
        max_length: Maximum allowed query length (default: 100KB)

    Raises:
        HTTPException: If query exceeds maximum length
    """
    if len(sql) > max_length:
        raise HTTPException(
            status_code=413,
            detail=f"SQL query exceeds maximum allowed length of {max_length} characters. Current length: {len(sql)} characters."
        )


def validate_parameter_name(param_name: str) -> bool:
    """
    Validate parameter name for prepared statements.

    Args:
        param_name: Parameter name to validate

    Returns:
        True if parameter name is valid

    Raises:
        HTTPException: If parameter name is invalid
    """
    if not param_name or not param_name.strip():
        raise HTTPException(
            status_code=400,
            detail="Parameter name cannot be empty"
        )

    if not PARAMETER_NAME_PATTERN.match(param_name):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid parameter name '{param_name}'. Parameter names must start with a letter or underscore and contain only letters, numbers, and underscores."
        )

    return True


def _get_df(conn: duckdb.DuckDBPyConnection, sql: str) -> pd.DataFrame:
    """Helper to robustly extract a pandas DataFrame from DuckDB, handling RecordBatchReader if needed."""
    try:
        # Most standard way in DuckDB 0.10+
        return conn.execute(sql).df()
    except Exception as e:
        logger.debug(f"Standard .df() failed: {e}. Attempting Arrow fallback.")
        try:
            # Fallback for complex results that might return as Arrow readers
            return conn.execute(sql).fetch_arrow_reader().read_all().to_pandas()
        except Exception as arrow_err:
            logger.error(f"Arrow fallback also failed: {arrow_err}")
            # Final attempt: try fetchdf()
            return conn.execute(sql).fetchdf()

@router.post("", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
@require_permission("workflows:create")
async def create_workflow(
    workflow_data: WorkflowCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new workflow.

    Requires permission: workflows:create
    """
    service = WorkflowService(db)

    # Get user ID from JWT token
    owner_id = int(current_user["sub"])

    workflow = await service.create_workflow(workflow_data, owner_id)
    return workflow

class WorkflowExecutionRequest(BaseModel):
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    preview_limit: Optional[int] = 50
    report_config: Optional[Dict[str, Any]] = None

@router.post("/save")
async def save_workflow_graph(
    request: WorkflowExecutionRequest,
    name: str = Query(...)
):
    """Save a workflow graph to a JSON file."""
    save_dir = "data/workflows"
    os.makedirs(save_dir, exist_ok=True)
    
    logger.info(f"Saving workflow: {name}")
    # Protect against path traversal
    safe_name = os.path.basename(name).replace(".json", "")
    file_path = os.path.join(save_dir, f"{safe_name}.json")
    with open(file_path, "w") as f:
        json.dump(request.dict(), f)
    
    return {"message": f"Workflow saved as {name}", "filename": f"{name}.json"}

@router.post("/rename")
async def rename_workflow(
    old_name: str = Query(...),
    new_name: str = Query(...)
):
    """Rename a saved workflow file."""
    save_dir = "data/workflows"
    # Protect against path traversal
    old_safe = os.path.basename(old_name).replace(".json", "")
    new_safe = os.path.basename(new_name).replace(".json", "")
    
    old_path = os.path.join(save_dir, f"{old_safe}.json")
    new_path = os.path.join(save_dir, f"{new_safe}.json")
    
    if not os.path.exists(old_path):
        raise HTTPException(status_code=404, detail="Original workflow not found")
    
    if os.path.exists(new_path):
        raise HTTPException(status_code=400, detail="A workflow with the new name already exists")
    
    os.rename(old_path, new_path)
    return {"message": f"Workflow renamed from {old_name} to {new_name}"}

@router.post("/delete")
async def delete_workflow(
    name: str = Query(...),
):
    """Delete a saved workflow file."""
    save_dir = "data/workflows"
    # Protect against path traversal
    safe_name = os.path.basename(name).replace(".json", "")
    file_path = os.path.join(save_dir, f"{safe_name}.json")

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Workflow not found")

    os.remove(file_path)
    return {"message": f"Workflow '{name}' deleted"}


@router.get("/list")
async def list_saved_workflows():
    """List all saved workflow graphs."""
    save_dir = "data/workflows"
    os.makedirs(save_dir, exist_ok=True)
    
    files = [f.replace(".json", "") for f in os.listdir(save_dir) if f.endswith(".json")]
    return {"workflows": sorted(files)}


class SqlValidationRequest(BaseModel):
    sql: str
    input_table: Optional[str] = None  # Deprecated: Use input_tables instead
    columns: Optional[List[Any]] = None  # Deprecated: Use input_tables instead
    input_tables: Optional[List[Dict[str, Any]]] = None  # NEW: Multi-input support

    class Config:
        # For backwards compatibility, allow extra fields
        extra = "allow"

class SqlPreviewRequest(BaseModel):
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    node_id: str
    sql: str
    preview_limit: Optional[int] = 50

@router.post("/preview-sql")
async def preview_sql(request: SqlPreviewRequest):
    """Execute a raw SQL query within the context of a specific node."""
    target_id = request.node_id
    nodes, edges = request.nodes, request.edges
    raw_sql = request.sql
    limit = request.preview_limit or 50

    # Validate SQL query length to prevent DoS
    validate_sql_query_length(raw_sql)

    # Validate node_id to prevent path traversal
    validate_parameter_name(target_id)

    logger.info(f">>> [PREVIEW SQL] Node: {target_id}, SQL Length: {len(raw_sql)}")

    # 1. Topological Sort up to target_id and its predecessors
    adj = {str(n["id"]): [] for n in nodes}
    predecessors = {str(n["id"]): [] for n in nodes}
    for edge in request.edges:
        src = str(edge.get("source", ""))
        target = str(edge.get("target", ""))
        if src in adj and target in adj:
            adj[src].append(target)
            predecessors[target].append(src)


    # We need to execute everything up to the predecessors of target_id
    preds = predecessors.get(target_id, [])
    
    # Actually, we can just use the execute_workflow_graph logic but intercept at target_id
    # To keep it simple and reliable, let's just use the same incremental execution logic
    
    # 2. Build Query node by node (Reuse logic from execute_workflow_graph)
    node_to_table = {} 
    try:
        conn = get_connection()
        
        # We need a sorted list of all nodes because we might need to execute they predecessors
        # but execute_workflow_graph already handles full graph.
        # Let's just run the full execution logic but only up to the predecessors we need.
        # Even better: just run the standard execution logic for the whole graph provided,
        # ensuring predecessors of target_id are ready.
        
        # Use a temporary WorkflowExecutionRequest to leverage the existing execution logic
        # but we need to avoid running the whole thing if possible.
        # However, execute_workflow_graph is fast due to caching.
        
        # Let's manually run the predecessors
        sorted_nodes = []
        visited = set()
        def _sort(nid):
            nid_str = str(nid)
            if nid_str in visited: return
            for p in predecessors.get(nid_str, []): _sort(p)
            visited.add(nid_str)
            obj = next((n for n in nodes if str(n["id"]) == nid_str), None)
            if obj: sorted_nodes.append(obj)
        
        for p_id in preds:
            _sort(p_id)
            
        # Execute predecessors
        for node in sorted_nodes:
            # This is a bit repetitive, but safest way to ensure environment is right
            # In a real app, we'd refactor execute_workflow_graph to be more modular.
            # For now, let's reuse the logic via a helper or just inline the essentials.
            
            # Since we want to stay within the same connection and use the same cache:
            # We can't easily call execute_workflow_graph because it returns a response.
            # But we can call it and ignore the result, then run our SQL.
            pass

        # Actually, let's just run execute_workflow_graph logic for the provided nodes/edges.
        # It's already cached, so it's super fast if already run.
        await execute_workflow_graph(WorkflowExecutionRequest(nodes=nodes, edges=edges, preview_limit=0))
        
        # Now find the input table(s) for target_id
        # We need to know what node_to_table would have for target_id
        # But node_to_table is local to exec_wf.
        # However, _NODE_CACHE is global!

        # 3. Execute the custom SQL with multi-input support
        processed_sql = raw_sql

        # Support multi-input placeholders: {{input1}}, {{input2}}, etc.
        # Replace based on predecessors in edge order
        for idx, pred_id in enumerate(preds, start=1):
            cached = _NODE_CACHE.get(pred_id)
            if cached:
                table_name = cached["table_name"]
                table_ref = f'"{table_name.replace('"', '""')}"'
                processed_sql = processed_sql.replace(f"{{{{input{idx}}}}}", table_ref)
                logger.info(f">>> [PREVIEW SQL] Replaced {{input{idx}}} with {table_ref}")

        # Backward compatible: {{input}} → first predecessor
        if "{{input}}" in processed_sql and preds:
            cached = _NODE_CACHE.get(preds[0])
            if cached:
                table_name = cached["table_name"]
                table_ref = f'"{table_name.replace('"', '""')}"'
                processed_sql = processed_sql.replace("{{input}}", table_ref)
                logger.info(f">>> [PREVIEW SQL] Replaced {{input}} with {table_ref}")

        # Auto-convert backticks to double quotes
        processed_sql = processed_sql.replace("`", "\"")
        logger.info(f">>> [PREVIEW SQL] Processed SQL: {processed_sql}")

        # Collect input table schemas for cache key generation
        input_schemas = {}
        for pred_id in preds:
            cached = _NODE_CACHE.get(pred_id)
            if cached and "schema" in cached:
                table_name = cached["table_name"]
                input_schemas[table_name] = cached["schema"]

        # Generate cache key and check for cached result
        cache_key = _generate_sql_cache_key(processed_sql, input_schemas)
        cached_result = _get_cached_sql_result(cache_key)

        if cached_result is not None:
            # Return cached result immediately
            logger.info(f">>> [PREVIEW SQL] Using cached result (cache hit)")
            return cached_result

        # Cache miss: execute the query
        df = _get_df(conn, processed_sql)

        result = {
            "status": "success",
            "columns": df.columns.tolist(),
            "preview": df.head(limit).fillna("").to_dict(orient="records"),
            "row_count": len(df)
        }

        # Cache the successful result
        _cache_sql_result(cache_key, result)

        return result
        
    except Exception as e:
        logger.error(f">>> [PREVIEW SQL] DuckDB ERROR: {str(e)}")
        user_message = map_duckdb_error_to_user_message(e)
        return {"status": "error", "message": user_message}

@router.post("/validate-sql")
async def validate_sql(
    request: SqlValidationRequest
):
    """Validate a DuckDB SQL query using EXPLAIN with multi-input support."""
    import re

    sql = request.sql
    input_tables = request.input_tables
    input_table = request.input_table  # Backward compatibility
    columns = request.columns  # Backward compatibility

    # Validate SQL query length to prevent DoS
    validate_sql_query_length(sql)

    # Normalize input_tables to always be a list
    tables_to_process = []

    if input_tables:
        # New multi-input format - Use what the frontend provided!
        tables_to_process = input_tables
        logger.info(f">>> [VALIDATE] Multi-input mode: {len(tables_to_process)} tables")
    elif input_table and columns:
        # Legacy single-input format - convert to new format
        tables_to_process = [{"name": input_table, "columns": columns}]
        logger.info(">>> [VALIDATE] Legacy single-input mode detected, converting")

    # If NO tables were provided, try auto-detection as a last resort
    if not tables_to_process:
        # Auto-detect multi-input placeholders
        pattern = r'\{\{input(\d+)\}\}'
        matches = re.findall(pattern, sql)
        # Also detect {{input}} pattern (single input)
        has_single_input = bool(re.search(r'\{\{input\}\}', sql))

        if matches:
            # Multi-input placeholders detected - extract column names from SQL
            max_input = max(int(m) for m in matches)
            logger.info(f">>> [VALIDATE] Auto-detected {max_input} inputs from SQL placeholders")

            input_columns = {}
            for i in range(1, max_input + 1):
                input_ref = f"input{i}"
                # Improved regex to support Korean characters and optional quotes
                col_patterns = [
                    rf'\{{\{{input{i}\}}}}\."?([a-zA-Z0-9_\uAC00-\uD7A3]+)"?',
                    rf'"{input_ref}"\."?([a-zA-Z0-9_\uAC00-\uD7A3]+)"?',
                    rf'{input_ref}\."?([a-zA-Z0-9_\uAC00-\uD7A3]+)"?',
                ]

                columns_found = set()
                for p in col_patterns:
                    found = re.findall(p, sql)
                    columns_found.update(found)

                sql_keywords = {'where', 'from', 'join', 'on', 'and', 'or', 'select', 'group', 'order', 'by', 'having', 'limit', 'as', 'is', 'null', 'not', 'in', 'like', 'between'}
                columns_found = {c for c in columns_found if c.lower() not in sql_keywords}

                if columns_found:
                    input_columns[input_ref] = list(columns_found)
                else:
                    input_columns[input_ref] = ['col']

            for i in range(1, max_input + 1):
                input_ref = f"input{i}"
                cols = input_columns.get(input_ref, ['col'])
                tables_to_process.append({
                    "name": input_ref,
                    "columns": [{"column_name": col, "column_type": "VARCHAR"} for col in cols]
                })

        elif has_single_input:
            input_ref = "input_1"
            col_patterns = [
                r'\{\{input\}\}\."?([a-zA-Z0-9_\uAC00-\uD7A3]+)"?',
                rf'"{input_ref}"\."?([a-zA-Z0-9_\uAC00-\uD7A3]+)"?',
                rf'{input_ref}\."?([a-zA-Z0-9_\uAC00-\uD7A3]+)"?',
            ]

            columns_found = set()
            for p in col_patterns:
                found = re.findall(p, sql)
                columns_found.update(found)

            sql_keywords = {'where', 'from', 'join', 'on', 'and', 'or', 'select', 'group', 'order', 'by', 'having', 'limit', 'as', 'is', 'null', 'not', 'in', 'like', 'between'}
            columns_found = {c for c in columns_found if c.lower() not in sql_keywords}

            cols = list(columns_found) if columns_found else ['col']
            tables_to_process.append({
                "name": input_ref,
                "columns": [{"column_name": col, "column_type": "VARCHAR"} for col in cols]
            })
            logger.info(">>> [VALIDATE] Auto-detected single {{input}} placeholder")

    logger.info(f">>> [VALIDATE] SQL Request received (Length: {len(sql)})")
    logger.info(f">>> [VALIDATE] Processing {len(tables_to_process)} input tables")

    try:
        conn = duckdb.connect(database=':memory:')

        # Build dummy tables for schema validation
        for table_info in tables_to_process:
            table_name = table_info.get("name", "")
            table_columns = table_info.get("columns", [])

            if not table_name:
                continue

            cols_def = []
            for col_item in table_columns:
                try:
                    # Handle both JSON string and already-parsed dict/list
                    c = col_item
                    if isinstance(col_item, str):
                        try:
                            c = json.loads(col_item)
                        except:
                            c = {"name": col_item, "type": "VARCHAR"}

                    if isinstance(c, dict):
                        # Try multiple possible keys for name and type
                        cname = c.get("column_name") or c.get("name") or c.get("id")
                        ctype = c.get("column_type") or c.get("type") or c.get("dtype", "VARCHAR")
                    else:
                        # Fallback to plain string column name cast to VARCHAR
                        cname = str(col_item)
                        ctype = "VARCHAR"

                    # Sanitize and add to definitions
                    if cname and str(cname).strip() and str(cname) != "dtype":
                        cols_def.append(f"CAST(NULL AS {ctype}) as {quote_identifier(str(cname))}")
                except Exception as e:
                    logger.warning(f"Failed to parse column for validation: {col_item} - {e}")

            # If no valid columns were parsed, use a safe default instead of failing
            if not cols_def:
                logger.info(f">>> [VALIDATE] No valid columns for table '{table_name}', using generic column")
                cols_def = ["CAST(NULL AS VARCHAR) as col"]

            # Create dummy table
            create_sql = f"CREATE OR REPLACE TABLE {quote_identifier(table_name)} AS SELECT {', '.join(cols_def)} WHERE 1=0"
            logger.info(f">>> [VALIDATE] Schema SQL: {create_sql}")
            conn.execute(create_sql)

        # Replace multi-input placeholders: {{input1}}, {{input2}}, etc.
        processed_sql = sql
        for idx, table_info in enumerate(tables_to_process, start=1):
            table_name = table_info.get("name", f"input_{idx}")
            safe_ref = f'"{table_name.replace('"', '""')}"'
            processed_sql = processed_sql.replace(f"{{{{input{idx}}}}}", safe_ref)

        # Backward compatible: {{input}} → first table
        if "{{input}}" in processed_sql and tables_to_process:
            table_name = tables_to_process[0].get("name", "input_1")
            safe_ref = f'"{table_name.replace('"', '""')}"'
            processed_sql = processed_sql.replace("{{input}}", safe_ref)

        # Fix REPLACE() calls for numeric columns
        # Collect schemas from all predecessors to fix REPLACE(column, ',', '') calls
        schemas_to_fix = {}
        for table_info in tables_to_process:
            if "schema" in table_info:
                schemas_to_fix.update(table_info["schema"])

        if schemas_to_fix:
            processed_sql = fix_replace_for_numeric_columns(processed_sql, schemas_to_fix)
            logger.info(f">>> [VALIDATE] Fixed REPLACE calls for {len(schemas_to_fix)} columns")

        # Auto-convert backticks to double quotes
        processed_sql = processed_sql.replace("`", "\"")

        logger.info(f">>> [VALIDATE] Processed SQL: {processed_sql[:200]}...")

        # Validate syntax and binder via EXPLAIN
        conn.execute(f"EXPLAIN {processed_sql}")
        return {"status": "success", "message": "SQL is valid"}
    except Exception as e:
        logger.error(f">>> [VALIDATE] DuckDB ERROR: {str(e)}")
        user_message = map_duckdb_error_to_user_message(e)
        return {"status": "error", "message": user_message}

@router.get("/load/{name}")
async def load_workflow_graph(name: str):
    """Load a specific workflow graph."""
    file_path = os.path.join("data/workflows", f"{name}.json")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Workflow not found")
        
    with open(file_path, "r") as f:
        data = json.load(f)
    return data

@router.post("/execute", status_code=status.HTTP_200_OK)
async def execute_workflow_graph(
    request: WorkflowExecutionRequest
):
    """
    Execute a raw workflow graph directly using DuckDB.
    """
    logger.info(f"Executing workflow with {len(request.nodes)} nodes and {len(request.edges)} edges.")

    # Invalidate SQL result cache when workflow is executed
    # This ensures stale results are not used if data has changed
    _invalidate_sql_cache_for_table("workflow_execution")

    # Locate nodes by subtype or label
    output_node = next((n for n in request.nodes if n["type"] == "output"), None)
    
    adj = {str(node["id"]): [] for node in request.nodes}
    predecessors = {str(node["id"]): [] for node in request.nodes}
    for edge in request.edges:
        src = str(edge.get("source", ""))
        target = str(edge.get("target", ""))
        if src in adj and target in adj:
            adj[src].append(target)
            predecessors[target].append(src)
            
    # 2. Topological Sort with Cycle Detection
    sorted_nodes = []
    visited = set()
    currently_visiting = set()
    
    def sort_nodes(node_id):
        node_id_str = str(node_id)
        if node_id_str in currently_visiting:
            raise HTTPException(status_code=400, detail=f"Circular dependency detected at node '{node_id_str}'.")
        if node_id_str in visited:
            return
            
        currently_visiting.add(node_id_str)
        for p_id in predecessors.get(node_id_str, []):
            sort_nodes(p_id)
        currently_visiting.remove(node_id_str)
        
        visited.add(node_id_str)
        node_obj = next((n for n in request.nodes if str(n["id"]) == node_id_str), None)
        if node_obj:
            sorted_nodes.append(node_obj)
            
    for node in request.nodes:
        sort_nodes(str(node["id"]))
        
    # 3. Build Query node by node with Incremental Caching
    node_to_table = {} 
    
    logger.info(f"--- Workflow Execution Start: {len(sorted_nodes)} nodes ---")

    try:
        conn = get_connection()

        for i, node in enumerate(sorted_nodes):
            node_id = str(node["id"])
            safe_id = node_id.replace("-", "_")
            table_name = f"node_{safe_id}"
            node_data = node.get("data", {})
            subtype = node_data.get("subtype")
            label = node_data.get("label", "")
            config = node_data.get("config", {})

            preds = predecessors.get(node_id, [])
            prev_table = node_to_table.get(preds[0]) if preds else None
            
            # --- Incremental Caching Logic ---
            # Generate a hash for this node based on its config and its predecessor tables/hashes
            input_hashes = [f"{p}:{_NODE_CACHE.get(p, {}).get('hash', 'root')}" for p in preds]
            node_state = {"config": config, "inputs": input_hashes, "subtype": subtype, "type": node["type"]}
            
            # Use deterministic hash
            import hashlib
            node_state_str = json.dumps(node_state, sort_keys=True)
            node_hash = hashlib.sha256(node_state_str.encode()).hexdigest()
            
            # Check cache
            cached = _NODE_CACHE.get(node_id)
            if cached and cached["hash"] == node_hash:
                # Table should already exist in memory
                try:
                    conn.execute(f"SELECT 1 FROM {cached['table_name']} LIMIT 0")
                    logger.info(f"Node {label} (ID: {node_id}) recovered from cache.")
                    node_to_table[node_id] = cached["table_name"]
                    continue
                except:
                    logger.info(f"Cache hit but table {cached['table_name']} missing. Re-executing...")
            
            # If not cached, execute and update cache
            logger.info(f"Processing node {i+1}/{len(sorted_nodes)}: {label}")
            
            if node["type"] == "input":
                if subtype == "remote_file":
                    url = config.get("url")
                    if not url: continue
                    try:
                        # Ensure httpfs is loaded for remote URLs
                        conn.execute("INSTALL httpfs; LOAD httpfs;")
                        
                        if url.lower().endswith('.parquet'):
                            conn.execute(f"CREATE OR REPLACE TEMP TABLE {table_name} AS SELECT * FROM read_parquet('{url}')")
                        else:
                            # Try CSV first
                            # Treat empty strings as NULL during CSV load
                            conn.execute(f"CREATE OR REPLACE TEMP TABLE {table_name} AS SELECT * FROM read_csv_auto('{url}', ALL_VARCHAR=TRUE, nullstr='')")
                        node_to_table[node_id] = table_name
                    except Exception as e:
                        logger.error(f"Failed to load remote file {url}: {e}")
                    continue

                file_path = config.get("file_path")
                logger.info(f">>> [INPUT NODE] Processing CSV file: {file_path}")
                if not file_path: continue
                if not os.path.isabs(file_path):
                    file_path = os.path.abspath(file_path)
                logger.info(f">>> [INPUT NODE] Absolute file path: {file_path}")
                logger.info(f">>> [INPUT NODE] File exists: {os.path.exists(file_path)}")

                load_format = config.get("format", "flat")
                if load_format == "kv":
                    # Schema-discovery for KV format (Union of all detected keys)
                    import csv
                    records = []
                    all_keys = set()
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        reader = csv.reader(f)
                        for row in reader:
                            if not row: continue
                            rec = {'id': row[0], 'timestamp': row[-1]}
                            for item in row[1:-1]:
                                if ':' in item:
                                    k, _, v = item.partition(':')
                                    rec[k.strip()] = v.strip()
                                    all_keys.add(k.strip())
                            records.append(rec)
                    
                    if records:
                        # DDL
                        columns = sorted(list(all_keys))
                        col_defs = ", ".join([f'"{c}" VARCHAR' for c in columns])
                        if col_defs: col_defs = ", " + col_defs
                        conn.execute(f"CREATE OR REPLACE TABLE {table_name} (id VARCHAR, timestamp VARCHAR {col_defs})")
                        
                        # Insert
                        all_cols = ["id", "timestamp"] + columns
                        placeholders = ", ".join(["?" for _ in all_cols])
                        insert_sql = f"INSERT INTO {table_name} ({', '.join([f'\"{c}\"' for c in all_cols])}) VALUES ({placeholders})"
                        
                        for rec in records:
                            vals = [rec.get(c, '') for c in all_cols]
                            conn.execute(insert_sql, vals)
                        
                        node_to_table[node_id] = table_name
                    else:
                        # Use schema inference for automatic type detection
                        infer_result = get_or_infer_csv_schema(file_path)
                        schema = infer_result["schema"]
                        encoding = infer_result.get("encoding", "utf-8")

                        if schema:
                            # Build CAST expressions with proper types
                            # Load with ALL_VARCHAR first, then SELECT with CAST expressions
                            temp_view = f"{table_name}_raw"

                            # Treat empty strings as NULL during CSV load
                            # Note: read_csv_auto automatically detects encoding
                            conn.execute(f"CREATE OR REPLACE TEMP TABLE {temp_view} AS SELECT * FROM read_csv_auto(?, ALL_VARCHAR=TRUE, nullstr='')", [file_path])

                            # Get actual column names from the loaded table to handle BOM/whitespace issues
                            # Use fetchall() to avoid .df() conversion issues
                            res = conn.execute(f"DESCRIBE {temp_view}")
                            actual_cols = [row[0] for row in res.fetchall()]

                            cast_exprs = build_cast_expressions(schema, temp_view, actual_cols=actual_cols)
                            conn.execute(f"CREATE OR REPLACE TEMP TABLE {table_name} AS SELECT {', '.join(cast_exprs)} FROM {temp_view}")
                            conn.execute(f"DROP TABLE IF EXISTS {temp_view}")

                            logger.info(f">>> [CSV LOAD] Created table {table_name} with {len(schema)} typed columns (encoding: {encoding})")

                            # Store schema in cache for raw_sql processing
                            # Use a temporary node cache entry that will be overwritten later
                            _NODE_CACHE[node_id] = _NODE_CACHE.get(node_id, {})
                            _NODE_CACHE[node_id]["schema"] = schema
                        else:
                            # Fallback to ALL_VARCHAR if schema inference fails
                            # Load into temp view first, then create final table with NULLIF for empty string handling
                            temp_view = f"{table_name}_raw"
                            conn.execute(f"CREATE OR REPLACE TEMP TABLE {temp_view} AS SELECT * FROM read_csv_auto(?, ALL_VARCHAR=TRUE, nullstr='')", [file_path])

                            # Get column names and create NULLIF expressions for all columns
                            res = conn.execute(f"DESCRIBE {temp_view}").df()
                            actual_cols = res['column_name'].tolist()

                            # Build SELECT with NULLIF for all columns to convert empty strings to NULL
                            nullif_exprs = [f"NULLIF(TRIM(CAST({quote_identifier(col)} AS VARCHAR)), '') AS {quote_identifier(col)}" for col in actual_cols]
                            conn.execute(f"CREATE OR REPLACE TEMP TABLE {table_name} AS SELECT {', '.join(nullif_exprs)} FROM {temp_view}")
                            conn.execute(f"DROP TABLE IF EXISTS {temp_view}")
                            logger.info(f">>> [CSV LOAD] Created table {table_name} with NULLIF handling (schema inference failed)")
                        node_to_table[node_id] = table_name
                else:
                        # Standard Flat loading with schema inference
                        infer_result = get_or_infer_csv_schema(file_path)
                        schema = infer_result["schema"]
                        encoding = infer_result.get("encoding", "utf-8")

                        if schema:
                            # Use schema inference for automatic type detection
                            temp_view = f"{table_name}_raw"
                            # Treat empty strings as NULL during CSV load
                            # Note: read_csv_auto automatically detects encoding
                            conn.execute(f"CREATE OR REPLACE TEMP TABLE {temp_view} AS SELECT * FROM read_csv_auto(?, ALL_VARCHAR=TRUE, nullstr='')", [file_path])

                            # Get actual column names from the loaded table to handle BOM/whitespace issues
                            # Use fetchall() to avoid .df() conversion issues
                            res = conn.execute(f"DESCRIBE {temp_view}")
                            actual_cols = [row[0] for row in res.fetchall()]

                            cast_exprs = build_cast_expressions(schema, temp_view, actual_cols=actual_cols)
                            conn.execute(f"CREATE OR REPLACE TEMP TABLE {table_name} AS SELECT {', '.join(cast_exprs)} FROM {temp_view}")
                            conn.execute(f"DROP TABLE IF EXISTS {temp_view}")

                            logger.info(f">>> [CSV LOAD] Created table {table_name} with {len(schema)} typed columns")

                            # Store schema in cache for raw_sql processing
                            _NODE_CACHE[node_id] = _NODE_CACHE.get(node_id, {})
                            _NODE_CACHE[node_id]["schema"] = schema
                        else:
                            # Fallback to ALL_VARCHAR if schema inference fails
                            # Load into temp view first, then create final table with NULLIF for empty string handling
                            temp_view = f"{table_name}_raw"
                            conn.execute(f"CREATE OR REPLACE TEMP TABLE {temp_view} AS SELECT * FROM read_csv_auto(?, ALL_VARCHAR=TRUE, nullstr='')", [file_path])

                            # Get column names and create NULLIF expressions for all columns
                            res = conn.execute(f"DESCRIBE {temp_view}").df()
                            actual_cols = res['column_name'].tolist()

                            # Build SELECT with NULLIF for all columns to convert empty strings to NULL
                            nullif_exprs = [f"NULLIF(TRIM(CAST({quote_identifier(col)} AS VARCHAR)), '') AS {quote_identifier(col)}" for col in actual_cols]
                            conn.execute(f"CREATE OR REPLACE TEMP TABLE {table_name} AS SELECT {', '.join(nullif_exprs)} FROM {temp_view}")
                            conn.execute(f"DROP TABLE IF EXISTS {temp_view}")
                            logger.info(f">>> [CSV LOAD] Created table {table_name} with NULLIF handling (schema inference failed)")

                        node_to_table[node_id] = table_name
                
            elif subtype == "filter" or "Filter" in label:
                if not prev_table: continue
                
                is_adv = config.get("isAdvanced", False)
                where = ""
                
                if is_adv:
                    where = config.get("customWhere", "")
                    # Validate WHERE clause to prevent SQL injection
                    if where:
                        validate_sql_fragment(conn, where, "WHERE")
                else:
                    col = config.get("column")
                    op = config.get("operator", "==")
                    val = str(config.get("value", "")).strip()
                    
                    if col:
                        clean_val = val.replace("'", "''")
                        qc = quote_identifier(col)
                        if op == "==": where = f"TRIM(CAST({qc} AS VARCHAR)) = '{clean_val}'"
                        elif op == "!=": where = f"(TRIM(CAST({qc} AS VARCHAR)) != '{clean_val}' OR {qc} IS NULL)"
                        elif op == "contains": where = f"CAST({qc} AS VARCHAR) ILIKE '%{clean_val}%'"
                        elif op == "not_contains": where = f"(TRIM(CAST({qc} AS VARCHAR)) NOT ILIKE '%{clean_val}%' OR {qc} IS NULL)"
                        elif op == "starts_with": where = f"CAST({qc} AS VARCHAR) ILIKE '{clean_val}%'"
                        elif op == "ends_with": where = f"CAST({qc} AS VARCHAR) ILIKE '%{clean_val}'"
                        elif op == "is_null": where = f"({qc} IS NULL OR CAST({qc} AS VARCHAR) = '')"
                        elif op == "is_not_null": where = f"({qc} IS NOT NULL AND CAST({qc} AS VARCHAR) != '')"
                        elif op == "in":
                            items = ["'" + v.strip().replace("'", "''") + "'" for v in val.split(',')]
                            where = f"TRIM(CAST({qc} AS VARCHAR)) IN ({', '.join(items)})"
                        elif op == "not_in":
                            items = ["'" + v.strip().replace("'", "''") + "'" for v in val.split(',')]
                            where = f"(TRIM(CAST({qc} AS VARCHAR)) NOT IN ({', '.join(items)}) OR {qc} IS NULL)"
                        elif op in [">", "<", ">=", "<="]:
                            num_val = clean_val.replace(',', '')
                            # Validate that the value is actually numeric
                            try:
                                float(num_val)
                                where = f"TRY_CAST(REPLACE(CAST({qc} AS VARCHAR), ',', '') AS DOUBLE) {op} {num_val}"
                            except ValueError:
                                raise HTTPException(
                                    status_code=400,
                                    detail=f"Invalid numeric value for comparison: '{clean_val}'. Operator {op} requires a numeric value."
                                )
                
                if where:
                    conn.execute(f"CREATE OR REPLACE TEMP TABLE {table_name} AS SELECT * FROM {prev_table} WHERE {where}")
                    node_to_table[node_id] = table_name
                else:
                    node_to_table[node_id] = prev_table
            
            elif subtype == "computed":
                if not prev_table: continue
                expr = config.get("expression")
                alias = config.get("alias", "new_column")
                if expr and alias:
                    # Validate expression to prevent SQL injection
                    validate_sql_fragment(conn, expr, "expression")
                    conn.execute(f"CREATE OR REPLACE TEMP TABLE {table_name} AS SELECT *, {expr} AS {quote_identifier(alias)} FROM {prev_table}")
                    node_to_table[node_id] = table_name
                else:
                    node_to_table[node_id] = prev_table

            elif subtype == "raw_sql":
                raw_sql = config.get("sql", "")
                if raw_sql:
                    # Support multi-input placeholders: {{input1}}, {{input2}}, etc.
                    all_preds = predecessors.get(node_id, [])
                    processed_sql = raw_sql

                    # Replace indexed placeholders
                    for idx, pred_id in enumerate(all_preds, start=1):
                        cached = _NODE_CACHE.get(pred_id)
                        if cached:
                            table_ref = f'"{cached["table_name"].replace('"', '""')}"'
                            processed_sql = processed_sql.replace(f"{{{{input{idx}}}}}", table_ref)

                    # Backward compatible: {{input}} → first predecessor
                    if "{{input}}" in processed_sql and all_preds:
                        cached = _NODE_CACHE.get(all_preds[0])
                        if cached:
                            table_ref = f'"{cached["table_name"].replace('"', '""')}"'
                            processed_sql = processed_sql.replace("{{input}}", table_ref)
                        elif prev_table:
                            # Fallback to prev_table if no predecessors
                            table_ref = f'"{prev_table.replace('"', '""')}"'
                            processed_sql = processed_sql.replace("{{input}}", table_ref)

                    # Fix REPLACE() calls for numeric columns
                    # Collect schemas from all predecessors to fix REPLACE(column, ',', '') calls
                    schemas_to_fix = {}
                    for pred_id in all_preds:
                        cached = _NODE_CACHE.get(pred_id, {})
                        if "schema" in cached:
                            schemas_to_fix.update(cached["schema"])

                    if schemas_to_fix:
                        processed_sql = fix_replace_for_numeric_columns(processed_sql, schemas_to_fix)
                        logger.info(f">>> [EXECUTE] Fixed REPLACE calls for {len(schemas_to_fix)} columns with schema info")

                    # Auto-convert backticks to double quotes for standard DuckDB support
                    processed_sql = processed_sql.replace("`", "\"")
                    conn.execute(f"CREATE OR REPLACE TEMP TABLE {table_name} AS {processed_sql}")
                    node_to_table[node_id] = table_name
                else:
                    node_to_table[node_id] = prev_table

            elif subtype == "distinct":
                if not prev_table: continue
                cols_raw = config.get("columns", "")
                if cols_raw:
                    cols = [quote_identifier(c.strip()) for c in cols_raw.split(',') if c.strip()]
                    conn.execute(f"CREATE OR REPLACE TEMP TABLE {table_name} AS SELECT DISTINCT {', '.join(cols)} FROM {prev_table}")
                else:
                    conn.execute(f"CREATE OR REPLACE TEMP TABLE {table_name} AS SELECT DISTINCT * FROM {prev_table}")
                node_to_table[node_id] = table_name

            elif subtype == "rename":
                if not prev_table: continue
                mappings = config.get("mappings", [])
                if mappings:
                    # Use fetchall() to avoid .df() conversion issues
                    res = conn.execute(f"DESCRIBE {prev_table}")
                    all_cols = [row[0] for row in res.fetchall()]
                    # Build renamed map with string conversion safety
                    renamed_map = {}
                    for m in mappings:
                        old_col = m.get('old')
                        new_col = m.get('new')
                        if old_col and new_col:
                            try:
                                old_str = str(old_col)
                                new_str = str(new_col)
                                renamed_map[old_str] = new_str
                            except Exception:
                                logger.warning(f">>> [RENAME] Skipping invalid mapping: {old_col} -> {new_col}")
                    select_items = [f"{quote_identifier(col)} AS {quote_identifier(renamed_map[col])}" if col in renamed_map else quote_identifier(col) for col in all_cols]
                    conn.execute(f"CREATE OR REPLACE TEMP TABLE {table_name} AS SELECT {', '.join(select_items)} FROM {prev_table}")
                    node_to_table[node_id] = table_name
                else:
                    node_to_table[node_id] = prev_table

            elif subtype == "case_when":
                if not prev_table: continue
                conditions = config.get("conditions", [])
                else_val_raw = str(config.get("elseValue", "NULL")).strip()
                alias = config.get("alias", "case_result")
                
                def sql_val(v):
                    if v is None: return "NULL"
                    if isinstance(v, (int, float)): return str(v)
                    if not isinstance(v, str): v = str(v)
                    if not v or v.upper() == "NULL": return "NULL"
                    if (v.startswith("'") and v.endswith("'")) or (v.startswith('"') and v.endswith('"')): return v
                    try:
                        # Ensure we call replace on a string
                        sv = str(v)
                        float(sv.replace(',', ''))
                        return sv
                    except ValueError:
                        return "'" + v.replace("'", "''") + "'"

                if conditions and alias:
                    case_parts = ["CASE"]
                    for c in conditions:
                        w, t = c.get('when'), c.get('then')
                        if w and t:
                            # Validate WHEN clause to prevent SQL injection
                            validate_sql_fragment(conn, w, "WHEN")
                            case_parts.append(f"WHEN {w} THEN {sql_val(t)}")
                    case_parts.append(f"ELSE {sql_val(else_val_raw)} END AS {quote_identifier(alias)}")
                    conn.execute(f"CREATE OR REPLACE TEMP TABLE {table_name} AS SELECT *, {' '.join(case_parts)} FROM {prev_table}")
                    node_to_table[node_id] = table_name
                else:
                    node_to_table[node_id] = prev_table

            elif subtype == "window":
                if not prev_table: continue
                func_name = config.get("function", "ROW_NUMBER")
                partition = config.get("partitionBy", "")
                order = config.get("orderBy", "")
                direction = config.get("direction", "ASC")
                alias = config.get("alias", "window_result")
                value_col = config.get("valueColumn", "")

                # Validate partitionBy and orderBy are simple identifiers, not expressions
                # This prevents SQL injection through complex expressions
                if partition and not is_simple_identifier(partition):
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid partitionBy column: '{partition}'. Must be a simple column name, not an expression."
                    )
                if order and not is_simple_identifier(order):
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid orderBy column: '{order}'. Must be a simple column name, not an expression."
                    )

                # Allowlist validation (prevent SQL injection)
                ALLOWED_FUNCS = {
                    "ROW_NUMBER", "RANK", "DENSE_RANK",
                    "LAG", "LEAD",
                    "SUM", "AVG", "MIN", "MAX", "COUNT"
                }
                if func_name not in ALLOWED_FUNCS:
                    logger.warning(f"Invalid window function '{func_name}', falling back to ROW_NUMBER")
                    func_name = "ROW_NUMBER"
                if direction not in ("ASC", "DESC"):
                    direction = "ASC"

                # Build function call: parameterless vs column-based
                PARAMETERLESS_FUNCS = {"ROW_NUMBER", "RANK", "DENSE_RANK"}
                if func_name in PARAMETERLESS_FUNCS:
                    func_call = f"{func_name}()"
                else:
                    if value_col:
                        func_call = f"{func_name}({quote_identifier(value_col)})"
                    else:
                        logger.warning(f"Window function {func_name} requires a valueColumn — skipping node")
                        node_to_table[node_id] = prev_table
                        continue

                over_parts = []
                if partition: over_parts.append(f"PARTITION BY {quote_identifier(partition)}")
                if order: over_parts.append(f"ORDER BY {quote_identifier(order)} {direction}")

                sql = (
                    f"CREATE OR REPLACE TEMP TABLE {table_name} AS "
                    f"SELECT *, {func_call} OVER ({' '.join(over_parts)}) AS {quote_identifier(alias)} "
                    f"FROM {prev_table}"
                )
                logger.info(f"Window SQL: {sql}")
                conn.execute(sql)
                node_to_table[node_id] = table_name

            elif subtype == "pivot":
                if not prev_table: continue
                on_col = config.get("on", "")
                using_expr = config.get("using", "")
                group_by = config.get("groupBy", "")
                if on_col and using_expr:
                    sql = f"CREATE OR REPLACE TEMP TABLE {table_name} AS PIVOT {prev_table} ON {quote_identifier(on_col)} USING {using_expr}"
                    if group_by:
                        groups = ", ".join([quote_identifier(c.strip()) for c in group_by.split(",") if c.strip()])
                        sql += f" GROUP BY {groups}"
                    logger.info(f"Pivot SQL: {sql}")
                    conn.execute(sql)
                    node_to_table[node_id] = table_name
                else:
                    node_to_table[node_id] = prev_table

            elif subtype == "unpivot":
                if not prev_table: continue
                on_cols = config.get("on", "")
                into_name = config.get("intoName", "name")
                into_value = config.get("intoValue", "value")
                if on_cols:
                    cols = ", ".join([quote_identifier(c.strip()) for c in on_cols.split(",") if c.strip()])
                    sql = f"CREATE OR REPLACE TEMP TABLE {table_name} AS UNPIVOT {prev_table} ON {cols} INTO NAME {quote_identifier(into_name)} VALUE {quote_identifier(into_value)}"
                    logger.info(f"Unpivot SQL: {sql}")
                    conn.execute(sql)
                    node_to_table[node_id] = table_name
                else:
                    node_to_table[node_id] = prev_table

            elif subtype == "sample":
                if not prev_table: continue
                method = config.get("method", "PERCENT")
                val = config.get("value", 10)
                if method == "ROWS":
                    sql = f"CREATE OR REPLACE TEMP TABLE {table_name} AS SELECT * FROM {prev_table} USING SAMPLE {val} ROWS"
                else:
                    sql = f"CREATE OR REPLACE TEMP TABLE {table_name} AS SELECT * FROM {prev_table} USING SAMPLE {val} PERCENT"
                logger.info(f"Sample SQL: {sql}")
                conn.execute(sql)
                node_to_table[node_id] = table_name

            elif subtype == "unnest":
                if not prev_table: continue
                col = config.get("column", "")
                alias = config.get("alias", "unnested_value")
                if col:
                    sql = f"CREATE OR REPLACE TEMP TABLE {table_name} AS SELECT * EXCLUDE ({quote_identifier(col)}), UNNEST({quote_identifier(col)}) AS {quote_identifier(alias)} FROM {prev_table}"
                    logger.info(f"Unnest SQL: {sql}")
                    conn.execute(sql)
                    node_to_table[node_id] = table_name
                else:
                    node_to_table[node_id] = prev_table

            elif subtype == "sort" or "Sort" in label:
                if not prev_table: continue
                col = config.get("column")
                direction = config.get("direction", "asc").upper()
                if col:
                    conn.execute(f"CREATE OR REPLACE TEMP TABLE {table_name} AS SELECT * FROM {prev_table} ORDER BY {quote_identifier(col)} {direction}")
                    node_to_table[node_id] = table_name
                else:
                    node_to_table[node_id] = prev_table
                    
            elif subtype == "limit" or "Limit" in label:
                if not prev_table: continue
                count = int(config.get("count", 100))
                conn.execute(f"CREATE OR REPLACE TEMP TABLE {table_name} AS SELECT * FROM {prev_table} LIMIT {count}")
                node_to_table[node_id] = table_name
                
            elif subtype == "clean" or "Clean" in label:
                if not prev_table: continue
                col, op = config.get("column"), config.get("operation", "trim")
                if col:
                    expr = quote_identifier(col)
                    if op == "trim": expr = f"TRIM(CAST({quote_identifier(col)} AS VARCHAR))"
                    elif op == "upper": expr = f"UPPER(CAST({quote_identifier(col)} AS VARCHAR))"
                    elif op == "lower": expr = f"LOWER(CAST({quote_identifier(col)} AS VARCHAR))"
                    elif op == "numeric": expr = f"REGEXP_REPLACE(CAST({quote_identifier(col)} AS VARCHAR), '[^0-9.]', '', 'g')"
                    elif op == "replace_null": expr = f"COALESCE(NULLIF(CAST({quote_identifier(col)} AS VARCHAR), ''), '{config.get('newValue', '')}')"
                    elif op == "to_date": expr = f"TRY_CAST({quote_identifier(col)} AS DATE)"
                    conn.execute(f"CREATE OR REPLACE TEMP TABLE {table_name} AS SELECT * REPLACE ({expr} AS {quote_identifier(col)}) FROM {prev_table}")
                    node_to_table[node_id] = table_name
                else:
                    node_to_table[node_id] = prev_table
                    
            elif subtype == "select" or "Select" in label:
                if not prev_table: continue
                cols = [c.strip() for c in config.get("columns", "").split(',') if c.strip()]
                if cols:
                    conn.execute(f"CREATE OR REPLACE TEMP TABLE {table_name} AS SELECT {', '.join([quote_identifier(c) for c in cols])} FROM {prev_table}")
                    node_to_table[node_id] = table_name
                else:
                    node_to_table[node_id] = prev_table
                    
            elif subtype == "combine" or "Combine" in label:
                if len(preds) < 2:
                    node_to_table[node_id] = prev_table
                else:
                    left, right = node_to_table.get(preds[0]), node_to_table.get(preds[1])
                    if left and right:
                        join_type = config.get("joinType", "inner").upper()
                        if join_type in ["UNION", "UNION_ALL", "APPEND"]:
                            # Handle UNION (combining rows)
                            op = "UNION ALL" if join_type in ["UNION_ALL", "APPEND"] else "UNION"
                            conn.execute(f"CREATE OR REPLACE TEMP TABLE {table_name} AS SELECT * FROM {left} {op} SELECT * FROM {right}")
                            node_to_table[node_id] = table_name
                        else:
                            # Handle JOIN (combining columns)
                            lc, rc = config.get("leftColumn"), config.get("rightColumn")
                            if lc and rc:
                                conn.execute(f"CREATE OR REPLACE TEMP TABLE {table_name} AS SELECT * FROM {left} {join_type} JOIN {right} ON {left}.{quote_identifier(lc)} = {right}.{quote_identifier(rc)}")
                                node_to_table[node_id] = table_name
                            else:
                                node_to_table[node_id] = left
                    else:
                        node_to_table[node_id] = prev_table

            elif subtype == "aggregate" or "Aggregate" in label:
                if not prev_table: continue
                group_by = [c.strip() for c in config.get("groupBy", "").split(',') if c.strip()]
                aggs = config.get("aggregations", [])
                if not aggs:
                    op_raw = config.get("operation") or "sum"
                    op = str(op_raw).upper()
                    aggs = [{"column": config.get("column"), "operation": op, "alias": config.get("alias")}]

                agg_parts = []
                for a in aggs:
                    c, f = a.get("column"), a.get("operation", "sum").upper()
                    al = a.get("alias") or f"{f.lower()}_{c}"
                    if c:
                        qc = quote_identifier(c)
                        qa = quote_identifier(al)
                        clean = f"TRY_CAST(REPLACE(CAST({qc} AS VARCHAR), ',', '') AS DOUBLE)"
                        agg_parts.append(f"COUNT({qc}) AS {qa}" if f == "COUNT" else f"{f}({clean}) AS {qa}")
                    else:
                        agg_parts.append(f"COUNT(*) AS {quote_identifier(al)}")

                sel = ", ".join(agg_parts)
                if group_by: sel = f"{', '.join([quote_identifier(c) for c in group_by])}, {sel}"
                sql = f"CREATE OR REPLACE TEMP TABLE {table_name} AS SELECT {sel} FROM {prev_table}"
                if group_by: sql += f" GROUP BY {', '.join([quote_identifier(c) for c in group_by])}"
                conn.execute(sql)
                node_to_table[node_id] = table_name

            elif node["type"] == "output":
                if subtype == "db_write":
                    if prev_table:
                        target_name = config.get("tableName", "my_table")
                        if target_name:
                            conn.execute(f"CREATE OR REPLACE TABLE {quote_identifier(target_name)} AS SELECT * FROM {prev_table}")
                        node_to_table[node_id] = target_name if target_name else prev_table
                else:
                    if prev_table: node_to_table[node_id] = prev_table

            if node_id not in node_to_table and prev_table:
                node_to_table[node_id] = prev_table

            # Finalize Cached State
            final_table = node_to_table.get(node_id)
            if final_table:
                import time
                # Preserve existing schema information if present
                existing_cache = _NODE_CACHE.get(node_id, {})
                cache_entry = {
                    "hash": node_hash,
                    "table_name": final_table,
                    "timestamp": time.time()
                }
                # Preserve schema if it exists in cache
                if "schema" in existing_cache:
                    cache_entry["schema"] = existing_cache["schema"]
                else:
                    # For transformation nodes, infer and cache schema
                    # This enables downstream nodes to benefit from type detection
                    try:
                        desc_df = _get_df(conn, f"DESCRIBE {final_table}")
                        inferred_schema = {}
                        for _, row in desc_df.iterrows():
                            # Extract column name and type safely
                            col_name_raw = row['column_name']
                            col_type_raw = row['column_type']

                            # Convert to strings, handling non-scalar types
                            try:
                                col_name = str(col_name_raw) if col_name_raw is not None else ""
                                col_type = str(col_type_raw) if col_type_raw is not None else "VARCHAR"
                            except Exception:
                                logger.warning(f">>> [CACHE] Skipping invalid column: {col_name_raw}")
                                continue

                            inferred_schema[col_name] = col_type
                        cache_entry["schema"] = inferred_schema
                        logger.info(f">>> [CACHE] Inferred schema for node {node_id}: {len(inferred_schema)} columns")
                    except Exception as e:
                        logger.warning(f">>> [CACHE] Failed to infer schema for node {node_id}: {e}")
                _NODE_CACHE[node_id] = cache_entry

        if not sorted_nodes:
            return {
                "status": "success",
                "row_count": 0,
                "preview": [],
                "columns": [],
                "message": "No nodes processed."
            }

        final_node_id = str(sorted_nodes[-1]["id"])
        final_table = node_to_table.get(final_node_id)
        # If no output node specified, use the last executed node's table
        if not final_table and node_to_table:
            # Get the last node in topological order that has a table
            for node in reversed(sorted_nodes):
                node_key = str(node["id"])
                if node_key in node_to_table:
                    final_table = node_to_table[node_key]
                    break

        if not final_table:
            raise HTTPException(status_code=400, detail="No output determined.")
        df = _get_df(conn, f"SELECT * FROM {final_table}")
        
        export_url = None
        if output_node:
            os.makedirs("downloads", exist_ok=True)
            config = output_node.get("data", {}).get("config", {})
            filename = config.get("filename", "exported_results.csv")
            if not filename.endswith('.csv'): filename += '.csv'
            export_path = os.path.join("downloads", f"export_{uuid.uuid4()}_{filename}")
            df.to_csv(export_path, index=False)
            export_url = f"/api/v1/data/download/{os.path.basename(export_path)}"

        node_counts, node_columns, node_samples, node_types = {}, {}, {}, {}
        preview_limit = request.preview_limit or 50
        
        for nid, tname in node_to_table.items():
            nid = str(nid)
            try:
                node_counts[nid] = conn.execute(f"SELECT COUNT(*) FROM {tname}").fetchone()[0]
                # Log column information for debugging
                desc_df = _get_df(conn, f"DESCRIBE {tname}")
                node_columns[nid] = desc_df['column_name'].tolist()
                node_types[nid] = desc_df[['column_name', 'column_type']].to_dict(orient='records')
                
                logger.info(f">>> [FLOW] Node {nid} ({tname}) cols: {node_columns[nid]}")
                
                node_samples[nid] = _get_df(conn, f"SELECT * FROM {tname} LIMIT {preview_limit}").fillna("").to_dict(orient="records")
            except:
                pass

        return {
            "status": "success",
            "row_count": len(df),
            "node_counts": node_counts,
            "node_columns": node_columns,
            "node_types": node_types,
            "node_samples": node_samples,
            "preview": df.head(preview_limit).fillna("").to_dict(orient="records"),
            "columns": df.columns.tolist(),
            "export_url": export_url
        }
    except Exception as e:
        logger.error(f"DuckDB Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.post("/report", status_code=status.HTTP_200_OK)
async def generate_workflow_report(
    request: WorkflowExecutionRequest
):
    """Generate a PDF or Markdown report from the workflow results."""
    logger.info(">>> [REPORT] Starting generation...")
    
    # 1. Execute workflow
    try:
        logger.info(f">>> [REPORT] Executing workflow with {len(request.nodes)} nodes...")
        exec_result = await execute_workflow_graph(request)
    except Exception as e:
        logger.error(f">>> [REPORT] Execution failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Workflow execution failed: {str(e)}")
    
    export_url = exec_result.get("export_url")
    if not export_url:
        logger.error(">>> [REPORT] No export URL found in execution results.")
        raise HTTPException(status_code=400, detail="Workflow must output data to generate a report.")
    
    file_name = os.path.basename(export_url)
    # Check downloads first (since we just moved exports there)
    file_path = os.path.join("downloads", file_name)
    if not os.path.exists(file_path):
        # Fallback to uploads for backward compatibility
        file_path = os.path.join("uploads", file_name)
        
    logger.info(f">>> [REPORT] Reading data from {file_path}...")
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Execution result file not found.")
        
    try:
        df = duckdb.read_csv(file_path).df()
        logger.info(f">>> [REPORT] Data loaded: {len(df)} rows.")
    except Exception as e:
        logger.error(f">>> [REPORT] Failed to read CSV: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to read data: {str(e)}")
    
    cfg = request.report_config or {}
    report_format = cfg.get("format", "PDF").upper()
    title = cfg.get("title", "Data Analysis Report")
    description = cfg.get("description", "")
    sections = cfg.get("sections", [])
    font_family = cfg.get("font", "NanumGothic")
    
    # Register font if needed
    font_path = "fonts/NanumGothic.ttf"
    is_korean = os.path.exists(font_path)
    if is_korean:
        try:
            pdfmetrics.registerFont(TTFont('NanumGothic', font_path))
        except:
            is_korean = False
    
    actual_font = font_family if (font_family == 'NanumGothic' and is_korean) else 'Helvetica'
    
    report_filename = f"report_{uuid.uuid4()}"
    
    if report_format == "MARKDOWN":
        os.makedirs("downloads", exist_ok=True)
        md_file = f"{report_filename}.md"
        md_path = os.path.join("downloads", md_file)
        
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(f"# {title}\n\n")
            if description:
                f.write(f"{description}\n\n")
            
            for sec in sections:
                f.write(f"## {sec.get('heading', 'Section')}\n\n")
                sec_type = sec.get("type", "table")
                
                if sec_type == "table":
                    f.write(df.head(20).to_markdown(index=False) + "\n\n")
                    if len(df) > 20:
                        f.write(f"*Note: Showing first 20 rows of {len(df)} total.*\n\n")
                elif sec_type == "stats":
                    f.write(df.describe().reset_index().to_markdown(index=False) + "\n\n")
                elif sec_type == "text":
                    content = sec.get("content", "")
                    content = content.replace("{{row_count}}", str(len(df)))
                    content = content.replace("{{column_count}}", str(len(df.columns)))
                    f.write(f"{content}\n\n")
            
            f.write(f"---\n*Generated by DuckDB Platform on {uuid.uuid1()}*")
            
        return {"status": "success", "report_url": f"/api/v1/data/download/{md_file}"}
        
    else: # PDF
        os.makedirs("downloads", exist_ok=True)
        pdf_file = f"{report_filename}.pdf"
        pdf_path = os.path.join("downloads", pdf_file)
        
        doc = SimpleDocTemplate(pdf_path, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()
        
        # Custom styles for Korean support
        title_style = ParagraphStyle(
            'TitleKR',
            parent=styles['Title'],
            fontName=actual_font,
            fontSize=24,
            spaceAfter=20
        )
        heading_style = ParagraphStyle(
            'HeadingKR',
            parent=styles['Heading2'],
            fontName=actual_font,
            fontSize=16,
            spaceAfter=12,
            spaceBefore=12
        )
        body_style = ParagraphStyle(
            'BodyKR',
            parent=styles['Normal'],
            fontName=actual_font,
            fontSize=10,
            leading=14
        )
        
        elements.append(Paragraph(title, title_style))
        if description:
            elements.append(Paragraph(description, body_style))
            elements.append(Spacer(1, 20))
            
        for sec in sections:
            elements.append(Paragraph(sec.get('heading', 'Section'), heading_style))
            sec_type = sec.get("type", "table")
            
            if sec_type == "table":
                # Convert first 15 rows to printable table
                cols = df.columns.tolist()
                data = [cols]
                sample_rows = df.head(15).fillna("").values.tolist()
                data.extend(sample_rows)
                
                # Truncate cell content for PDF display
                clean_data = []
                for row in data:
                    clean_data.append([str(cell)[:20] for cell in row])
                
                t = RLTable(clean_data)
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, -1), actual_font),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                elements.append(t)
                if len(df) > 15:
                    elements.append(Paragraph(f"(Showing 15 of {len(df)} rows)", body_style))
                elements.append(Spacer(1, 15))
                
            elif sec_type == "stats":
                stats_df = df.describe().reset_index()
                cols = stats_df.columns.tolist()
                data = [cols] + stats_df.fillna("").values.tolist()
                clean_data = [[str(cell)[:20] for cell in row] for row in data]
                
                t = RLTable(clean_data)
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('FONTNAME', (0, 0), (-1, -1), actual_font),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
                ]))
                elements.append(t)
                elements.append(Spacer(1, 15))
                
            elif sec_type == "text":
                content = sec.get("content", "")
                content = content.replace("{{row_count}}", str(len(df)))
                content = content.replace("{{column_count}}", str(len(df.columns)))
                elements.append(Paragraph(content, body_style))
                elements.append(Spacer(1, 15))
        
        doc.build(elements)
        return {"status": "success", "report_url": f"/api/v1/data/download/{pdf_file}"}

class InspectRequest(BaseModel):
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    node_id: str

@router.post("/inspect", status_code=status.HTTP_200_OK)
async def inspect_node_dataset(request: InspectRequest):
    """Run full statistical inspection on a specific node's output dataset."""
    target_id = request.node_id
    nodes, edges = request.nodes, request.edges

    adj = {str(n["id"]): [] for n in nodes}
    predecessors = {str(n["id"]): [] for n in nodes}
    for edge in edges:
        src = str(edge.get("source", ""))
        target = str(edge.get("target", ""))
        if src in adj and target in adj:
            adj[src].append(target)
            predecessors[target].append(src)

    sorted_nodes: list = []
    visited: set = set()
    def _sort(nid: str):
        nid_str = str(nid)
        if nid_str in visited: return
        for p in predecessors.get(nid_str, []):
            _sort(p)
        visited.add(nid_str)
        obj = next((n for n in nodes if str(n["id"]) == nid_str), None)
        if obj: sorted_nodes.append(obj)
    _sort(str(target_id))

    try:
        conn = get_connection()
        node_to_table: dict = {}

        for node in sorted_nodes:
            node_id = str(node["id"])
            safe_id = node_id.replace("-", "_")
            table_name = f"inspect_{safe_id}" # Use 'inspect_' prefix to avoid collisions with 'node_'
            node_data = node.get("data", {})
            subtype = node_data.get("subtype")
            label = node_data.get("label", "")
            config = node_data.get("config", {})
            preds = predecessors.get(node_id, [])
            prev_table = node_to_table.get(preds[0]) if preds else None

            try:
                if node["type"] == "input":
                    if subtype == "remote_file":
                        url = config.get("url")
                        if not url: continue
                        try:
                            # Ensure httpfs is loaded for remote URLs
                            conn.execute("INSTALL httpfs; LOAD httpfs;")
                            
                            if url.lower().endswith('.parquet'):
                                conn.execute(f"CREATE OR REPLACE TEMP TABLE {table_name} AS SELECT * FROM read_parquet('{url}')")
                            else:
                                # Try CSV first
                                # Treat empty strings as NULL during CSV load
                                conn.execute(f"CREATE OR REPLACE TEMP TABLE {table_name} AS SELECT * FROM read_csv_auto('{url}', ALL_VARCHAR=TRUE, nullstr='')")
                            node_to_table[node_id] = table_name
                        except Exception as e:
                            logger.error(f"Failed to load remote file {url}: {e}")
                        continue

                    fp = config.get("file_path")
                    if not fp: continue
                    if not os.path.isabs(fp): fp = os.path.abspath(fp)
                    
                    ext = os.path.splitext(fp)[1].lower()
                    if ext == '.parquet':
                        conn.execute(f"CREATE OR REPLACE TEMP TABLE {table_name} AS SELECT * FROM read_parquet('{fp}')")
                    elif ext in ['.xlsx', '.xls']:
                        # Try using the excel extension if available, otherwise fallback to spatial
                        try:
                            conn.execute("INSTALL excel; LOAD excel;")
                            conn.execute(f"CREATE OR REPLACE TEMP TABLE {table_name} AS SELECT * FROM st_read('{fp}')")
                        except Exception:
                            # Fallback to CSV with schema inference
                            infer_result = get_or_infer_csv_schema(fp)
                            schema = infer_result["schema"]
                            if schema:
                                temp_view = f"{table_name}_raw"
                                # Treat empty strings as NULL during CSV load
                                # Note: read_csv_auto automatically detects encoding
                                conn.execute(f"CREATE OR REPLACE TEMP TABLE {temp_view} AS SELECT * FROM read_csv_auto(?, ALL_VARCHAR=TRUE, nullstr='')", [fp])
                                
                                # Get actual column names to handle BOM/whitespace issues
                                res = conn.execute(f"DESCRIBE {temp_view}").df()
                                actual_cols = res['column_name'].tolist()

                                cast_exprs = build_cast_expressions(schema, temp_view, actual_cols=actual_cols)
                                conn.execute(f"CREATE OR REPLACE TEMP TABLE {table_name} AS SELECT {', '.join(cast_exprs)} FROM {temp_view}")
                                conn.execute(f"DROP TABLE IF EXISTS {temp_view}")
                            else:
                                # Final fallback to ALL_VARCHAR if schema inference fails
                                # Treat empty strings as NULL during CSV load
                                conn.execute(f"CREATE OR REPLACE TEMP TABLE {table_name} AS SELECT * FROM read_csv_auto(?, ALL_VARCHAR=TRUE, nullstr='')", [fp])
                    # Use schema-aware CSV loading with TRY_CAST for null handling
                    infer_result = get_or_infer_csv_schema(fp)
                    schema = infer_result["schema"]
                    if schema:
                        temp_view = f"{table_name}_raw"
                        # Treat empty strings as NULL during CSV load
                        # Note: read_csv_auto automatically detects encoding
                        conn.execute(f"CREATE OR REPLACE TEMP TABLE {temp_view} AS SELECT * FROM read_csv_auto(?, ALL_VARCHAR=TRUE, nullstr='')", [fp])

                        # Get actual column names to handle BOM/whitespace issues
                        res = conn.execute(f"DESCRIBE {temp_view}").df()
                        actual_cols = res['column_name'].tolist()

                        cast_exprs = build_cast_expressions(schema, temp_view, actual_cols=actual_cols)
                        conn.execute(f"CREATE OR REPLACE TEMP TABLE {table_name} AS SELECT {', '.join(cast_exprs)} FROM {temp_view}")
                        conn.execute(f"DROP TABLE IF EXISTS {temp_view}")
                    else:
                        # Fallback to DuckDB auto-detection if schema inference fails
                        # Load into temp view first, then create final table with NULLIF for empty string handling
                        temp_view = f"{table_name}_raw"
                        conn.execute(f"CREATE OR REPLACE TEMP TABLE {temp_view} AS SELECT * FROM read_csv_auto(?, ALL_VARCHAR=TRUE, nullstr='')", [fp])

                        # Get column names and create NULLIF expressions for all columns
                        res = conn.execute(f"DESCRIBE {temp_view}").df()
                        actual_cols = res['column_name'].tolist()

                        # Build SELECT with NULLIF for all columns to convert empty strings to NULL
                        nullif_exprs = [f"NULLIF(TRIM(CAST({quote_identifier(col)} AS VARCHAR)), '') AS {quote_identifier(col)}" for col in actual_cols]
                        conn.execute(f"CREATE OR REPLACE TEMP TABLE {table_name} AS SELECT {', '.join(nullif_exprs)} FROM {temp_view}")
                        conn.execute(f"DROP TABLE IF EXISTS {temp_view}")
                    node_to_table[node_id] = table_name
                elif prev_table:
                    # Pass-through execution for all transformation nodes
                    exec_req = WorkflowExecutionRequest(nodes=nodes, edges=edges, preview_limit=0)
                    # Re-use the single-node logic inline using a simplified pass
                    if subtype == "filter" or "Filter" in label:
                        is_adv = config.get("isAdvanced", False)
                        where = ""
                        if is_adv:
                            where = config.get("customWhere", "")
                            # Validate WHERE clause to prevent SQL injection
                            if where:
                                validate_sql_fragment(conn, where, "WHERE")
                        else:
                            col, op = config.get("column"), config.get("operator", "==")
                            val = str(config.get("value", "")).strip()
                            if col:
                                qc = quote_identifier(col)
                                cv = val.replace("'", "''")
                                if op == "==": where = f"TRIM(CAST({qc} AS VARCHAR)) = '{cv}'"
                                elif op == "!=": where = f"(TRIM(CAST({qc} AS VARCHAR)) != '{cv}' OR {qc} IS NULL)"
                                elif op == "contains": where = f"CAST({qc} AS VARCHAR) ILIKE '%{cv}%'"
                                elif op == "is_null": where = f"({qc} IS NULL OR CAST({qc} AS VARCHAR) = '')"
                                elif op == "is_not_null": where = f"({qc} IS NOT NULL AND CAST({qc} AS VARCHAR) != '')"
                                elif op in [">", "<", ">=", "<="]:
                                    num_val = cv.replace(',', '')
                                    # Validate numeric value
                                    try:
                                        float(num_val)
                                        where = f"TRY_CAST(REPLACE(CAST({qc} AS VARCHAR), ',', '') AS DOUBLE) {op} {num_val}"
                                    except ValueError:
                                        raise HTTPException(
                                            status_code=400,
                                            detail=f"Invalid numeric value for comparison: '{val}'. Operator {op} requires a numeric value."
                                        )
                        if where:
                            conn.execute(f"CREATE OR REPLACE TEMP TABLE {table_name} AS SELECT * FROM {prev_table} WHERE {where}")
                            node_to_table[node_id] = table_name
                        else: node_to_table[node_id] = prev_table
                    elif subtype == "select" or "Select" in label:
                        cols = [c.strip() for c in config.get("columns", "").split(',') if c.strip()]
                        if cols:
                            conn.execute(f"CREATE OR REPLACE TEMP TABLE {table_name} AS SELECT {', '.join([quote_identifier(c) for c in cols])} FROM {prev_table}")
                            node_to_table[node_id] = table_name
                        else: node_to_table[node_id] = prev_table
                    elif subtype == "aggregate" or "Aggregate" in label:
                        group_by = [c.strip() for c in config.get("groupBy", "").split(',') if c.strip()]
                        aggs = config.get("aggregations", []) or []
                        if not aggs: aggs = [{"column": config.get("column"), "operation": config.get("operation", "sum").upper(), "alias": config.get("alias")}]
                        agg_parts = []
                        for a in aggs:
                            c, f = a.get("column"), a.get("operation", "sum").upper()
                            al = a.get("alias") or f"{f.lower()}_{c}"
                            if c:
                                qc = quote_identifier(c)
                                qa = quote_identifier(al)
                                agg_parts.append(f"COUNT({qc}) AS {qa}" if f == "COUNT" else f"{f}(TRY_CAST(REPLACE(CAST({qc} AS VARCHAR), ',', '') AS DOUBLE)) AS {qa}")
                            else: agg_parts.append(f"COUNT(*) AS {quote_identifier(al)}")
                        sel = ", ".join(agg_parts)
                        if group_by: sel = f"{', '.join([quote_identifier(c) for c in group_by])}, {sel}"
                        sql = f"CREATE OR REPLACE TEMP TABLE {table_name} AS SELECT {sel} FROM {prev_table}"
                        if group_by: sql += f" GROUP BY {', '.join([quote_identifier(c) for c in group_by])}"
                        conn.execute(sql); node_to_table[node_id] = table_name
                    elif subtype == "pivot":
                        on_col = config.get("on", "")
                        using_expr = config.get("using", "")
                        group_by = config.get("groupBy", "")
                        if on_col and using_expr:
                            sql = f"CREATE OR REPLACE TEMP TABLE {table_name} AS PIVOT {prev_table} ON {quote_identifier(on_col)} USING {using_expr}"
                            if group_by:
                                sql += f" GROUP BY {', '.join([quote_identifier(c.strip()) for c in group_by.split(',') if c.strip()])}"
                            conn.execute(sql); node_to_table[node_id] = table_name
                        else: node_to_table[node_id] = prev_table
                    elif subtype == "unpivot":
                        on_cols = config.get("on", "")
                        into_name = config.get("intoName", "name")
                        into_value = config.get("intoValue", "value")
                        if on_cols:
                            cols = ", ".join([quote_identifier(c.strip()) for c in on_cols.split(",") if c.strip()])
                            sql = f"CREATE OR REPLACE TEMP TABLE {table_name} AS UNPIVOT {prev_table} ON {cols} INTO NAME {quote_identifier(into_name)} VALUE {quote_identifier(into_value)}"
                            conn.execute(sql); node_to_table[node_id] = table_name
                        else: node_to_table[node_id] = prev_table
                    elif subtype == "sample":
                        method = config.get("method", "PERCENT")
                        val = config.get("value", 10)
                        if method == "ROWS": sql = f"CREATE OR REPLACE TEMP TABLE {table_name} AS SELECT * FROM {prev_table} USING SAMPLE {val} ROWS"
                        else: sql = f"CREATE OR REPLACE TEMP TABLE {table_name} AS SELECT * FROM {prev_table} USING SAMPLE {val} PERCENT"
                        conn.execute(sql); node_to_table[node_id] = table_name
                    elif subtype == "unnest":
                        col = config.get("column", "")
                        alias = config.get("alias", "unnested_value")
                        if col:
                            sql = f"CREATE OR REPLACE TEMP TABLE {table_name} AS SELECT * EXCLUDE ({quote_identifier(col)}), UNNEST({quote_identifier(col)}) AS {quote_identifier(alias)} FROM {prev_table}"
                            conn.execute(sql); node_to_table[node_id] = table_name
                        else: node_to_table[node_id] = prev_table
                    elif subtype == "sort" or "Sort" in label:
                        col, direction = config.get("column"), config.get("direction", "asc").upper()
                        if col:
                            conn.execute(f"CREATE OR REPLACE TEMP TABLE {table_name} AS SELECT * FROM {prev_table} ORDER BY {quote_identifier(col)} {direction}")
                            node_to_table[node_id] = table_name
                        else:
                            node_to_table[node_id] = prev_table
                    elif subtype == "limit" or "Limit" in label:
                        conn.execute(f"CREATE OR REPLACE TEMP TABLE {table_name} AS SELECT * FROM {prev_table} LIMIT {int(config.get('count', 100))}")
                        node_to_table[node_id] = table_name
                    elif subtype == "raw_sql":
                        raw_sql = config.get("sql", "")
                        if raw_sql:
                            # Support multi-input placeholders: {{input1}}, {{input2}}, etc.
                            all_preds = predecessors.get(node_id, [])
                            processed_sql = raw_sql

                            # Replace indexed placeholders
                            for idx, pred_id in enumerate(all_preds, start=1):
                                cached = _NODE_CACHE.get(pred_id)
                                if cached:
                                    table_ref = f'"{cached["table_name"].replace('"', '""')}"'
                                    processed_sql = processed_sql.replace(f"{{{{input{idx}}}}}", table_ref)

                            # Backward compatible: {{input}} → first predecessor
                            if "{{input}}" in processed_sql and all_preds:
                                cached = _NODE_CACHE.get(all_preds[0])
                                if cached:
                                    table_ref = f'"{cached["table_name"].replace('"', '""')}"'
                                    processed_sql = processed_sql.replace("{{input}}", table_ref)
                            elif prev_table:
                                # Fallback to prev_table if no predecessors
                                table_ref = f'"{prev_table.replace('"', '""')}"'
                                processed_sql = processed_sql.replace("{{input}}", table_ref)

                            # Fix REPLACE() calls for numeric columns
                            # Collect schemas from all predecessors to fix REPLACE(column, ',', '') calls
                            schemas_to_fix = {}
                            for pred_id in all_preds:
                                cached = _NODE_CACHE.get(pred_id, {})
                                if "schema" in cached:
                                    schemas_to_fix.update(cached["schema"])

                            if schemas_to_fix:
                                processed_sql = fix_replace_for_numeric_columns(processed_sql, schemas_to_fix)
                                logger.info(f">>> [RAW SQL] Fixed REPLACE calls for {len(schemas_to_fix)} columns with schema info")

                            # Auto-convert backticks to double quotes for standard DuckDB support
                            processed_sql = processed_sql.replace("`", "\"")
                            conn.execute(f"CREATE OR REPLACE TEMP TABLE {table_name} AS {processed_sql}")
                            node_to_table[node_id] = table_name
                        else:
                            node_to_table[node_id] = prev_table
                    else:
                        node_to_table[node_id] = prev_table
                elif node["type"] == "output":
                    if prev_table: node_to_table[node_id] = prev_table
            except Exception as node_err:
                logger.warning(f"Inspect: node {node_id} failed: {node_err}")
                if prev_table: node_to_table[node_id] = prev_table

        target_table = node_to_table.get(target_id)
        if not target_table:
            raise HTTPException(status_code=400, detail=f"Could not execute workflow to reach node '{target_id}'.")

        total_rows = conn.execute(f"SELECT COUNT(*) FROM {target_table}").fetchone()[0]
        desc_df = _get_df(conn, f"DESCRIBE {target_table}")

        columns = []
        try:
            summarize_df = _get_df(conn, f"SUMMARIZE {target_table}")
            summarize_map = {}
            for _, row in summarize_df.iterrows():
                # Extract column name safely, ensuring it's a string
                col_name_raw = row.get('column_name', row['column_name'] if 'column_name' in row else None)
                if col_name_raw is not None:
                    try:
                        col_name = str(col_name_raw)
                        summarize_map[col_name] = row
                    except Exception:
                        logger.warning(f">>> [STATS] Skipping column with invalid name: {col_name_raw}")
        except Exception as e:
            logger.warning(f">>> [STATS] Failed to summarize table: {e}")
            summarize_map = {}

        def val_or_none(v):
            if v is None or pd.isna(v): return None
            try:
                fv = float(v)
                if not math.isfinite(fv): return None
                return fv
            except (ValueError, TypeError): pass
            if isinstance(v, (pd.Timestamp, pd.Period)):
                return str(v)
            return v

        for _, drow in desc_df.iterrows():
            col_name = drow['column_name']
            col_type = drow['column_type']
            stat: dict = {"column_name": col_name, "column_type": col_type}
            if col_name in summarize_map:
                s = summarize_map[col_name]
                # DuckDB SUMMARIZE 'count' is total count, not non-null count
                # Calculate non-null count from total count and null_percentage
                total_from_summarize = int(s.get('count', 0)) if val_or_none(s.get('count')) is not None else 0
                null_pct_from_summarize = float(s.get('null_percentage', 0)) if val_or_none(s.get('null_percentage')) is not None else 0
                cnt = int(total_from_summarize * (1 - null_pct_from_summarize / 100))
                logger.info(f">>> [STATS] Column '{col_name}': total={total_from_summarize}, null_pct={null_pct_from_summarize}, cnt={cnt}, null_count={total_rows - cnt}")
                stat.update({
                    "count": cnt,
                    "null_count": total_rows - cnt,
                    "null_pct": round((total_rows - cnt) / total_rows * 100, 1) if total_rows else 0,
                    "distinct": int(s.get('approx_unique', 0)) if val_or_none(s.get('approx_unique')) is not None else 0,
                    "min": str(s['min']) if val_or_none(s.get('min')) is not None else None,
                    "max": str(s['max']) if val_or_none(s.get('max')) is not None else None,
                    "mean": round(float(s['avg']), 4) if isinstance(val_or_none(s.get('avg')), (int, float)) else None,
                    "std": round(float(s['std']), 4) if isinstance(val_or_none(s.get('std')), (int, float)) else None,
                    "q25": str(s['q25']) if val_or_none(s.get('q25')) is not None else None,
                    "q50": str(s['q50']) if val_or_none(s.get('q50')) is not None else None,
                    "q75": str(s['q75']) if val_or_none(s.get('q75')) is not None else None,
                })
            else:
                # Column not in SUMMARIZE output (shouldn't happen, but handle it)
                try:
                    qcn = quote_identifier(col_name)
                    cnt = conn.execute(f"SELECT COUNT({qcn}) FROM {target_table}").fetchone()[0]
                    dist = conn.execute(f"SELECT COUNT(DISTINCT {qcn}) FROM {target_table}").fetchone()[0]
                    null_count = total_rows - cnt
                    logger.info(f">>> [STATS-ELSE] Column '{col_name}': total_rows={total_rows}, cnt={cnt}, null_count={null_count}")
                    stat.update({"count": cnt, "null_count": null_count,
                                 "null_pct": round((total_rows - cnt) / total_rows * 100, 1) if total_rows else 0,
                                 "distinct": dist})
                except Exception: pass
            columns.append(stat)

        def clean_json(v):
            if isinstance(v, float):
                if not math.isfinite(v): return None
                return v
            if isinstance(v, list): return [clean_json(i) for i in v]
            if isinstance(v, dict): return {ki: clean_json(vi) for ki, vi in v.items()}
            return v

        preview_limit = 50
        # Use fetchall() to avoid .df() conversion issues with empty strings
        res = conn.execute(f"SELECT * FROM {target_table} LIMIT {preview_limit}")
        columns_list = [desc[0] for desc in res.description]
        samples = [dict(zip(columns_list, [None if v is None or v == '' else v for v in row])) for row in res.fetchall()]

        return clean_json({
            "status": "success", 
            "total_rows": total_rows, 
            "total_columns": len(columns), 
            "columns": columns,
            "node_samples": samples
        })

    except HTTPException: raise
    except Exception as e:
        logger.error(f"Inspect error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Inspection error: {str(e)}")


@router.get("/column-types", status_code=status.HTTP_200_OK)
async def get_column_types(file_path: str):
    """
    Get detected column types for a CSV file

    Returns schema information including detected types for each column.
    Uses automatic type inference with Korean number format support.
    """
    try:
        # Validate file exists
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"File not found: {file_path}")

        # Get or infer schema (uses cache)
        infer_result = get_or_infer_csv_schema(file_path)
        schema = infer_result["schema"]

        if not schema:
            raise HTTPException(status_code=400, detail="Failed to infer schema from file")

        # Build column type information
        columns = []
        for col_name, col_type in schema.items():
            columns.append({
                "name": col_name,
                "detected_type": col_type,
                "can_override": True
            })

        logger.info(f">>> [COLUMN TYPES] Detected {len(columns)} columns for {file_path} (encoding: {infer_result.get('encoding')})")

        return {
            "status": "success",
            "file_path": file_path,
            "columns": columns,
            "total_columns": len(columns)
        }

    except HTTPException: raise
    except Exception as e:
        logger.error(f">>> [COLUMN TYPES] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting column types: {str(e)}")


@router.post("/analyze", status_code=status.HTTP_200_OK)
async def analyze_workflow_schema(request: WorkflowExecutionRequest):
    return SchemaAnalyzerService.analyze_workflow_schema(request)
@router.get("", response_model=WorkflowListResponse)
@require_permission("workflows:read")
async def list_workflows(
    is_active: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = WorkflowService(db)
    owner_id = int(current_user["sub"])
    workflows, total = await service.list_workflows(owner_id, is_active=is_active, page=page, page_size=page_size)
    return WorkflowListResponse(workflows=workflows, total=total, page=page, page_size=page_size)


@router.get("/{workflow_id}", response_model=WorkflowResponse)
@require_permission("workflows:read")
async def get_workflow(
    workflow_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = WorkflowService(db)
    owner_id = int(current_user["sub"])
    workflow = await service.get_workflow(workflow_id, owner_id)
    if not workflow: raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow


@router.put("/{workflow_id}", response_model=WorkflowResponse)
@require_permission("workflows:write")
async def update_workflow(
    workflow_id: str,
    workflow_data: WorkflowUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = WorkflowService(db)
    owner_id = int(current_user["sub"])
    workflow = await service.update_workflow(workflow_id, workflow_data, owner_id)
    if not workflow: raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow


@router.patch("/{workflow_id}", response_model=WorkflowResponse)
@require_permission("workflows:write")
async def partial_update_workflow(
    workflow_id: str,
    workflow_data: WorkflowUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = WorkflowService(db)
    owner_id = int(current_user["sub"])
    workflow = await service.update_workflow(workflow_id, workflow_data, owner_id)
    if not workflow: raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow


@router.delete("/{workflow_id}", status_code=status.HTTP_204_NO_CONTENT)
@require_permission("workflows:delete")
async def delete_workflow(
    workflow_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = WorkflowService(db)
    owner_id = int(current_user["sub"])
    success = await service.delete_workflow(workflow_id, owner_id)
    if not success: raise HTTPException(status_code=404, detail="Workflow not found")
    return None
