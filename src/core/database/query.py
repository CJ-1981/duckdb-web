"""
Query Builder for DuckDB

Type-safe query builder with parameterized queries to prevent SQL injection.
"""

from typing import List, Tuple, Dict, Any, Optional


class QueryBuilder:
    """
    Query builder for constructing parameterized SQL queries

    Features:
    - Type-safe query construction
    - Automatic parameterization
    - SQL injection prevention
    - Fluent interface
    """

    def __init__(self):
        """Initialize query builder"""
        self._query_type: Optional[str] = None
        self._table: Optional[str] = None
        self._columns: List[str] = []
        self._where_clauses: List[str] = []
        self._where_params: List[Any] = []
        self._set_values: Dict[str, Any] = {}
        self._insert_columns: List[str] = []
        self._insert_values: List[Any] = []
        self._join_clauses: List[str] = []
        self._order_by_clause: Optional[str] = None
        self._limit_value: Optional[int] = None
        self._offset_value: Optional[int] = None

    def select(self, table: str, columns: List[str] = None) -> "QueryBuilder":
        """
        Build SELECT query

        Args:
            table: Table name
            columns: Columns to select (default: all)

        Returns:
            Self for chaining
        """
        self._query_type = "SELECT"
        self._table = table
        self._columns = columns or ["*"]
        return self

    def insert(self, table: str) -> "QueryBuilder":
        """
        Build INSERT query

        Args:
            table: Table name

        Returns:
            Self for chaining
        """
        self._query_type = "INSERT"
        self._table = table
        return self

    def update(self, table: str) -> "QueryBuilder":
        """
        Build UPDATE query

        Args:
            table: Table name

        Returns:
            Self for chaining
        """
        self._query_type = "UPDATE"
        self._table = table
        return self

    def delete(self, table: str) -> "QueryBuilder":
        """
        Build DELETE query

        Args:
            table: Table name

        Returns:
            Self for chaining
        """
        self._query_type = "DELETE"
        self._table = table
        return self

    def where(self, clause: str, params: List[Any] = None) -> "QueryBuilder":
        """
        Add WHERE clause

        Args:
            clause: WHERE clause with ? placeholders
            params: Parameters for clause

        Returns:
            Self for chaining
        """
        self._where_clauses.append(clause)
        if params:
            self._where_params.extend(params)
        return self

    def and_where(self, clause: str, params: List[Any] = None) -> "QueryBuilder":
        """
        Add AND WHERE clause

        Args:
            clause: WHERE clause with ? placeholders
            params: Parameters for clause

        Returns:
            Self for chaining
        """
        self._where_clauses.append(f"AND {clause}")
        if params:
            self._where_params.extend(params)
        return self

    def or_where(self, clause: str, params: List[Any] = None) -> "QueryBuilder":
        """
        Add OR WHERE clause

        Args:
            clause: WHERE clause with ? placeholders
            params: Parameters for clause

        Returns:
            Self for chaining
        """
        self._where_clauses.append(f"OR {clause}")
        if params:
            self._where_params.extend(params)
        return self

    def set(self, values: Dict[str, Any]) -> "QueryBuilder":
        """
        Set values for UPDATE query

        Args:
            values: Dictionary of column-value pairs

        Returns:
            Self for chaining
        """
        self._set_values.update(values)
        return self

    def values(self, columns: List[str], values: List[Any]) -> "QueryBuilder":
        """
        Set values for INSERT query

        Args:
            columns: Column names
            values: Values to insert

        Returns:
            Self for chaining
        """
        self._insert_columns = columns
        self._insert_values = values
        return self

    def join(
        self, table: str, condition: str, join_type: str = "INNER"
    ) -> "QueryBuilder":
        """
        Add JOIN clause

        Args:
            table: Table to join
            condition: Join condition
            join_type: Type of join (INNER, LEFT, RIGHT, FULL)

        Returns:
            Self for chaining
        """
        self._join_clauses.append(f"{join_type} JOIN {table} ON {condition}")
        return self

    def order_by(self, column: str, direction: str = "ASC") -> "QueryBuilder":
        """
        Add ORDER BY clause

        Args:
            column: Column to order by
            direction: ASC or DESC

        Returns:
            Self for chaining
        """
        self._order_by_clause = f"ORDER BY {column} {direction}"
        return self

    def limit(self, count: int) -> "QueryBuilder":
        """
        Add LIMIT clause

        Args:
            count: Maximum number of rows

        Returns:
            Self for chaining
        """
        self._limit_value = count
        return self

    def offset(self, count: int) -> "QueryBuilder":
        """
        Add OFFSET clause

        Args:
            count: Number of rows to skip

        Returns:
            Self for chaining
        """
        self._offset_value = count
        return self

    def build(self) -> Tuple[str, List[Any]]:
        """
        Build the query and return SQL with parameters

        Returns:
            Tuple of (query_string, parameters)

        Raises:
            ValueError: If query is incomplete
        """
        if not self._query_type:
            raise ValueError("No query type specified")

        if self._query_type == "SELECT":
            return self._build_select()
        elif self._query_type == "INSERT":
            return self._build_insert()
        elif self._query_type == "UPDATE":
            return self._build_update()
        elif self._query_type == "DELETE":
            return self._build_delete()
        else:
            raise ValueError(f"Unknown query type: {self._query_type}")

    def _build_select(self) -> Tuple[str, List[Any]]:
        """Build SELECT query"""
        # SELECT column(s)
        query = f"SELECT {', '.join(self._columns)} FROM {self._table}"

        # JOINs
        if self._join_clauses:
            query += " " + " ".join(self._join_clauses)

        # WHERE
        params = list(self._where_params)
        if self._where_clauses:
            query += " WHERE " + " ".join(self._where_clauses)

        # ORDER BY
        if self._order_by_clause:
            query += " " + self._order_by_clause

        # LIMIT
        if self._limit_value is not None:
            query += f" LIMIT {self._limit_value}"

        # OFFSET
        if self._offset_value is not None:
            query += f" OFFSET {self._offset_value}"

        return query, params

    def _build_insert(self) -> Tuple[str, List[Any]]:
        """Build INSERT query"""
        if not self._insert_columns:
            raise ValueError("No columns specified for INSERT")

        columns_str = ", ".join(self._insert_columns)
        placeholders = ", ".join(["?" for _ in self._insert_columns])

        query = f"INSERT INTO {self._table} ({columns_str}) VALUES ({placeholders})"

        return query, list(self._insert_values)

    def _build_update(self) -> Tuple[str, List[Any]]:
        """Build UPDATE query"""
        if not self._set_values:
            raise ValueError("No values specified for UPDATE")

        # Build SET clause
        set_clauses = []
        params = []

        for column, value in self._set_values.items():
            set_clauses.append(f"{column} = ?")
            params.append(value)

        query = f"UPDATE {self._table} SET {', '.join(set_clauses)}"

        # WHERE
        if self._where_clauses:
            query += " WHERE " + " ".join(self._where_clauses)
            params.extend(self._where_params)

        return query, params

    def _build_delete(self) -> Tuple[str, List[Any]]:
        """Build DELETE query"""
        query = f"DELETE FROM {self._table}"

        # WHERE
        params = list(self._where_params)
        if self._where_clauses:
            query += " WHERE " + " ".join(self._where_clauses)

        return query, params

    def reset(self) -> "QueryBuilder":
        """Reset query builder for reuse"""
        self.__init__()
        return self
