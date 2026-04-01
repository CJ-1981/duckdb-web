"""
Database Exceptions

Custom exceptions for database operations.
"""


class DatabaseError(Exception):
    """Base exception for all database errors"""

    pass


class ConnectionError(DatabaseError):
    """Raised when database connection fails"""

    pass


class PoolExhaustedError(DatabaseError):
    """Raised when connection pool has no available connections"""

    pass


class QueryTimeoutError(DatabaseError):
    """Raised when query execution exceeds timeout"""

    pass


class QueryExecutionError(DatabaseError):
    """Raised when query execution fails"""

    pass


class ConnectionValidationError(DatabaseError):
    """Raised when connection validation fails"""

    pass
