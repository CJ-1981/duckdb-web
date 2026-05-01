"""
Structured Logging Configuration

Configures structlog for JSON-based structured logging with correlation IDs,
log levels, and contextual information for production environments.

Environment Variables:
    LOG_LEVEL: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    LOG_FORMAT: Log format (json, console) - defaults to json in production
    LOG_PRETTY: Enable pretty console output (true/false) - defaults to false
"""

import logging
import os
import sys
from typing import Any, Mapping

import structlog
from structlog.types import Processor, EventDict, WrappedLogger


def get_log_level() -> int:
    """
    Get log level from environment variable.

    Returns:
        Logging level constant (e.g., logging.INFO)

    Environment Variables:
        LOG_LEVEL: DEBUG, INFO, WARNING, ERROR, CRITICAL (default: INFO)
    """
    level_str = os.getenv("LOG_LEVEL", "INFO").upper()
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    return level_map.get(level_str, logging.INFO)


def is_production() -> bool:
    """
    Determine if running in production environment.

    Returns:
        True if production environment detected
    """
    return os.getenv("ENV", "development").lower() in ("production", "prod")


def is_json_format() -> bool:
    """
    Determine if JSON log format should be used.

    Returns:
        True if JSON format is configured
    """
    format_type = os.getenv("LOG_FORMAT", "json" if is_production() else "console").lower()
    return format_type == "json"


def is_pretty_print() -> bool:
    """
    Determine if pretty console output is enabled.

    Returns:
        True if pretty printing is enabled
    """
    return os.getenv("LOG_PRETTY", "false").lower() == "true"


def add_app_context(_logger: WrappedLogger, _method_name: str, event_dict: EventDict) -> Mapping[str, Any]:
    """
    Add application-level context to log entries.

    Args:
        logger: Logger instance
        method_name: Logging method name
        event_dict: Event dictionary to enhance

    Returns:
        Enhanced event dictionary with app context
    """
    # Add application name
    event_dict["app"] = "duckdb-processor"

    # Add environment
    event_dict["environment"] = os.getenv("ENV", "development")

    return event_dict


def add_request_info(_logger: WrappedLogger, _method_name: str, event_dict: EventDict) -> Mapping[str, Any]:
    """
    Extract and add request information from structlog context.

    Args:
        logger: Logger instance
        method_name: Logging method name
        event_dict: Event dictionary to enhance

    Returns:
        Enhanced event dictionary with request info
    """
    # Extract request_id if present in context
    if "request_id" in event_dict:
        request_id = event_dict.pop("request_id")
        event_dict["correlation_id"] = request_id

    # Extract other request context
    for key in ["path", "method", "status_code", "duration_ms"]:
        if key in event_dict:
            event_dict[f"http_{key}"] = event_dict.pop(key)

    return event_dict


def configure_logging() -> None:
    """
    Configure structured logging for the application.

    Sets up structlog with appropriate processors based on environment:
    - Production: JSON format with timestamp, level, correlation_id
    - Development: Console format with colors and pretty output

    Log format includes:
    - timestamp: ISO 8601 format
    - level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    - correlation_id: Request tracing ID
    - module: Python module name
    - message: Log message
    - context: Additional structured data
    """
    log_level = get_log_level()
    use_json = is_json_format()
    pretty_print = is_pretty_print()

    # Shared processors for all formats
    shared_processors: list[Processor] = [
        # Add log level
        structlog.stdlib.add_log_level,

        # Add timestamp in ISO format
        structlog.processors.TimeStamper(fmt="iso"),

        # Add application context
        add_app_context,

        # Add request information
        add_request_info,

        # Add call site information (file, line, function)
        structlog.processors.CallsiteParameterAdder(
            parameters=[
                structlog.processors.CallsiteParameter.FILENAME,
                structlog.processors.CallsiteParameter.LINENO,
                structlog.processors.CallsiteParameter.FUNC_NAME,
            ]
        ),
    ]

    if use_json:
        # Production: JSON format for log aggregation
        processors = shared_processors + [
            # Format exception as JSON
            structlog.processors.format_exc_info,

            # JSON renderer
            structlog.processors.JSONRenderer()
        ]
    else:
        # Development: Console format with colors
        processors = shared_processors + [
            # Format exception as string
            structlog.dev.ConsoleRenderer(
                colors=pretty_print,
                exception_formatter=structlog.dev.plain_traceback
            )
        ]

    # Configure structlog
    structlog.configure(
        processors=processors,

        # Wrapper class for standard library logging
        wrapper_class=structlog.make_filtering_bound_logger(log_level),

        # Context variables
        context_class=dict,

        # Logger factory
        logger_factory=structlog.PrintLoggerFactory(),

        # Cache context on logger
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )

    # Suppress noisy loggers
    for logger_name in ["uvicorn", "uvicorn.access", "uvicorn.error", "aiohttp"]:
        logging.getLogger(logger_name).setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Get a structured logger instance.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Structured logger instance

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("User logged in", user_id=123, ip="192.168.1.1")
    """
    return structlog.get_logger(name)


# Auto-configure logging on import
configure_logging()
