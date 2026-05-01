"""
Monitoring Package

Comprehensive production-ready monitoring and logging system for DuckDB web application.

Components:
    - logging_config: Structured JSON logging with correlation IDs
    - middleware: Request/response monitoring middleware
    - health: Kubernetes-style health check endpoints
    - metrics: Prometheus-compatible metrics collection

Quick Start:
    from src.api.monitoring.logging_config import get_logger
    from src.api.monitoring.metrics import MetricsMiddleware

    # Get structured logger
    logger = get_logger(__name__)
    logger.info("Application started", version="1.0.0")

    # Add metrics middleware to FastAPI app
    app.add_middleware(MetricsMiddleware)

Environment Variables:
    LOG_LEVEL: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    LOG_FORMAT: Log format (json, console)
    LOG_PRETTY: Enable pretty console output (true/false)
    SLOW_REQUEST_THRESHOLD_MS: Slow request warning threshold (default: 1000)
    PROMETHEUS_ENABLED: Enable Prometheus metrics endpoint (default: false)
    PROMETHEUS_PATH: Metrics endpoint path (default: /metrics)

Dependencies:
    structlog: Structured logging
    prometheus-client: Metrics collection (optional)

Integration:
    - Logging: JSON format compatible with ELK, Loki, CloudWatch
    - Health: Kubernetes probes for orchestration
    - Metrics: Prometheus scraping for Grafana dashboards
"""

from src.api.monitoring.logging_config import (
    get_logger,
    configure_logging,
    get_log_level,
)
from src.api.monitoring.middleware import (
    MonitoringMiddleware,
    RequestContextMiddleware,
)
from src.api.monitoring.health import router as health_router
from src.api.monitoring.metrics import (
    metrics,
    MetricsMiddleware,
    track_http_request,
    track_database_query,
    track_file_upload,
    track_sql_query,
    timed,
)


__all__ = [
    # Logging
    "get_logger",
    "configure_logging",
    "get_log_level",

    # Middleware
    "MonitoringMiddleware",
    "RequestContextMiddleware",
    "MetricsMiddleware",

    # Health Checks
    "health_router",

    # Metrics
    "metrics",
    "track_http_request",
    "track_database_query",
    "track_file_upload",
    "track_sql_query",
    "timed",
]
