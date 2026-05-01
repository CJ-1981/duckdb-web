"""
Application Metrics Collection

Prometheus-compatible metrics for monitoring application performance.
Tracks request metrics, database operations, and business metrics.

Environment Variables:
    PROMETHEUS_ENABLED: Enable Prometheus metrics endpoint (default: false)
    PROMETHEUS_PATH: Metrics endpoint path (default: /metrics)

Dependencies:
    prometheus_client: pip install prometheus-client

Integration:
    - Prometheus: Configure scrape target in prometheus.yml
    - Grafana: Import dashboards from Prometheus
    - AlertManager: Set up alerts based on metrics
"""

import time
from functools import wraps
from typing import Callable, TYPE_CHECKING

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from src.api.monitoring.logging_config import get_logger

# Try to import prometheus_client
if TYPE_CHECKING:
    from prometheus_client import Counter, Histogram, Gauge, Info

try:
    from prometheus_client import Counter, Histogram, Gauge, Info
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

    # Create stub classes for graceful degradation
    class _Counter:
        def __init__(self, *args, **kwargs):
            _ = args, kwargs  # Mark as intentionally unused
        def inc(self, _amount=1):
            pass
        def labels(self, **kwargs):
            return self

    class _Histogram:
        def __init__(self, *args, **kwargs):
            _ = args, kwargs  # Mark as intentionally unused
        def time(self):
            return self
        def __enter__(self):
            return self
        def __exit__(self, *_args):
            _ = _args  # Mark as intentionally unused
        def labels(self, **kwargs):
            return self
        def observe(self, _amount):
            pass

    class _Gauge:
        def __init__(self, *args, **kwargs):
            _ = args, kwargs  # Mark as intentionally unused
        def set(self, _value):
            pass
        def inc(self, _amount=1):
            pass
        def dec(self, _amount=1):
            pass
        def labels(self, **kwargs):
            return self

    class _Info:
        def __init__(self, *args, **kwargs):
            _ = args, kwargs  # Mark as intentionally unused
        def info(self, _info_dict):
            pass

    # Use stub classes when prometheus_client is not available
    Counter = _Counter  # type: ignore
    Histogram = _Histogram  # type: ignore
    Gauge = _Gauge  # type: ignore
    Info = _Info  # type: ignore


# Module logger
logger = get_logger(__name__)


class MetricsRegistry:
    """
    Centralized metrics registry for application metrics.

    Singleton pattern ensures consistent metric collection across
    the application.

    Metrics Categories:
    - HTTP: Request count, latency, error rate by endpoint
    - Database: Query timing, connection pool usage
    - Business: File uploads, SQL queries executed
    - System: Memory, CPU (if available)
    """

    _instance = None

    def __new__(cls):
        """Singleton pattern - ensure only one instance exists."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize metrics registry with Prometheus metrics."""
        if self._initialized:
            return

        if not PROMETHEUS_AVAILABLE:
            logger.warning("Prometheus client not available - metrics disabled")
            self._initialized = True
            return

        # HTTP Request Metrics
        self.http_requests_total = Counter(
            "http_requests_total",
            "Total HTTP requests",
            ["method", "endpoint", "status"]
        )

        self.http_request_duration_seconds = Histogram(
            "http_request_duration_seconds",
            "HTTP request latency",
            ["method", "endpoint"],
            buckets=(.005, .01, .025, .05, .075, .1, .25, .5, .75, 1.0, 2.5, 5.0, 7.5, 10.0, float('inf'))
        )

        self.http_requests_in_progress = Gauge(
            "http_requests_in_progress",
            "HTTP requests currently in progress",
            ["method", "endpoint"]
        )

        # Database Metrics
        self.db_queries_total = Counter(
            "db_queries_total",
            "Total database queries executed",
            ["query_type", "status"]
        )

        self.db_query_duration_seconds = Histogram(
            "db_query_duration_seconds",
            "Database query execution time",
            ["query_type"],
            buckets=(.001, .005, .01, .025, .05, .1, .25, .5, 1.0, 2.5, 5.0, float('inf'))
        )

        # Business Metrics
        self.file_uploads_total = Counter(
            "file_uploads_total",
            "Total file uploads processed",
            ["status", "file_type"]
        )

        self.sql_queries_total = Counter(
            "sql_queries_total",
            "Total SQL queries executed",
            ["query_type"]
        )

        # Application Info
        self.app_info = Info(
            "app_info",
            "Application information"
        )
        self.app_info.info({
            "version": "1.0.0",
            "name": "duckdb-processor"
        })

        self._initialized = True
        logger.info("Metrics registry initialized")


# Global metrics registry instance
metrics = MetricsRegistry()


def track_http_request(method: str, endpoint: str, status_code: int, duration: float):
    """
    Record HTTP request metrics.

    Args:
        method: HTTP method (GET, POST, etc.)
        endpoint: Request endpoint path
        status_code: HTTP response status code
        duration: Request duration in seconds
    """
    if not PROMETHEUS_AVAILABLE:
        return

    metrics.http_requests_total.labels(
        method=method,
        endpoint=endpoint,
        status=str(status_code)
    ).inc()

    metrics.http_request_duration_seconds.labels(
        method=method,
        endpoint=endpoint
    ).observe(duration)


def track_database_query(query_type: str, duration: float, success: bool = True):
    """
    Record database query metrics.

    Args:
        query_type: Type of query (select, insert, update, etc.)
        duration: Query execution time in seconds
        success: Whether the query succeeded
    """
    if not PROMETHEUS_AVAILABLE:
        return

    status = "success" if success else "error"

    metrics.db_queries_total.labels(
        query_type=query_type,
        status=status
    ).inc()

    metrics.db_query_duration_seconds.labels(
        query_type=query_type
    ).observe(duration)


def track_file_upload(status: str, file_type: str):
    """
    Record file upload metrics.

    Args:
        status: Upload status (success, error, validation_failed)
        file_type: File type (csv, parquet, json)
    """
    if not PROMETHEUS_AVAILABLE:
        return

    metrics.file_uploads_total.labels(
        status=status,
        file_type=file_type
    ).inc()


def track_sql_query(query_type: str):
    """
    Record SQL query execution.

    Args:
        query_type: Type of SQL query (select, aggregate, join)
    """
    if not PROMETHEUS_AVAILABLE:
        return

    metrics.sql_queries_total.labels(
        query_type=query_type
    ).inc()


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Prometheus metrics collection middleware.

    Automatically tracks HTTP request metrics for all endpoints.

    Metrics Collected:
    - http_requests_total: Request count by method, endpoint, status
    - http_request_duration_seconds: Request latency distribution
    - http_requests_in_progress: Concurrent requests gauge
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and collect metrics.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware or route handler

        Returns:
            HTTP response with metrics tracking
        """
        if not PROMETHEUS_AVAILABLE:
            return await call_next(request)

        # Extract endpoint path
        method = request.method
        # Use route path (e.g., /api/users/{user_id}) instead of actual path
        endpoint = request.url.path

        # Track in-progress requests
        metrics.http_requests_in_progress.labels(
            method=method,
            endpoint=endpoint
        ).inc()

        # Track timing
        start_time = time.time()

        try:
            response = await call_next(request)

            # Calculate duration
            duration = time.time() - start_time

            # Record metrics
            track_http_request(
                method=method,
                endpoint=endpoint,
                status_code=response.status_code,
                duration=duration
            )

            return response

        finally:
            # Decrement in-progress gauge
            metrics.http_requests_in_progress.labels(
                method=method,
                endpoint=endpoint
            ).dec()


def timed(query_type: str):
    """
    Decorator to time database queries and record metrics.

    Args:
        query_type: Type of query being timed

    Example:
        @timed("select")
        def get_user(user_id: int):
            return db.query(User).filter(User.id == user_id).first()
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                track_database_query(query_type, duration, success=True)
                return result
            except Exception as exc:
                duration = time.time() - start_time
                track_database_query(query_type, duration, success=False)
                raise exc

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                track_database_query(query_type, duration, success=True)
                return result
            except Exception as exc:
                duration = time.time() - start_time
                track_database_query(query_type, duration, success=False)
                raise exc

        # Return appropriate wrapper based on function type
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


__all__ = [
    "metrics",
    "track_http_request",
    "track_database_query",
    "track_file_upload",
    "track_sql_query",
    "MetricsMiddleware",
    "timed",
    "PROMETHEUS_AVAILABLE",
]
