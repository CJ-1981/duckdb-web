"""
Monitoring Middleware

Enhanced request/response logging middleware with structured logging,
performance tracking, and correlation ID propagation for production monitoring.

Middleware Stack Order:
    1. RequestIDMiddleware - Adds unique request ID
    2. MonitoringMiddleware - Structured logging and metrics
    3. ErrorHandlerMiddleware - Error handling (from main middleware)
"""

import os
import time
from typing import Callable

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from src.api.monitoring.logging_config import get_logger


# Module logger
logger = get_logger(__name__)


class MonitoringMiddleware(BaseHTTPMiddleware):
    """
    Enhanced monitoring middleware for production observability.

    Features:
    - Structured JSON logging with correlation IDs
    - Request/response timing metrics
    - Slow query detection (configurable threshold)
    - Error tracking with context
    - HTTP status code tracking

    Environment Variables:
        SLOW_REQUEST_THRESHOLD_MS: Threshold for slow request logging (default: 1000ms)

    Example Log Output (JSON):
        {
            "timestamp": "2026-05-01T12:34:56.789Z",
            "level": "INFO",
            "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
            "app": "duckdb-processor",
            "environment": "production",
            "http_path": "/api/workflows/execute",
            "http_method": "POST",
            "http_status_code": 200,
            "duration_ms": 234.5,
            "module": "monitoring.middleware",
            "message": "Request completed"
        }
    """

    def __init__(self, app):
        """
        Initialize monitoring middleware.

        Args:
            app: FastAPI application instance
        """
        super().__init__(app)

        # Load slow request threshold from environment (default: 1000ms)
        self.slow_request_threshold_ms = float(
            os.getenv("SLOW_REQUEST_THRESHOLD_MS", "1000")
        )

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and response with monitoring.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware or route handler

        Returns:
            HTTP response with monitoring headers
        """
        # Start timing
        start_time = time.time()

        # Get correlation ID from request state (set by RequestIDMiddleware)
        correlation_id = getattr(request.state, "request_id", "unknown")

        # Extract client information
        client_host = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")

        # Log request start
        logger.info(
            "Request started",
            path=request.url.path,
            method=request.method,
            correlation_id=correlation_id,
            client_host=client_host,
            user_agent=user_agent,
        )

        # Process request
        try:
            response = await call_next(request)

            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000

            # Add monitoring headers to response
            response.headers["X-Request-ID"] = correlation_id
            response.headers["X-Process-Time-Ms"] = f"{duration_ms:.2f}"

            # Log response based on status code
            if 200 <= response.status_code < 300:
                # Success: log at INFO level
                log_level = logger.info
            elif 300 <= response.status_code < 400:
                # Redirect: log at INFO level
                log_level = logger.info
            elif 400 <= response.status_code < 500:
                # Client error (4xx): log at WARNING level
                log_level = logger.warning
            else:
                # Server error (5xx): log at ERROR level
                log_level = logger.error

            log_level(
                "Request completed",
                path=request.url.path,
                method=request.method,
                status_code=response.status_code,
                duration_ms=round(duration_ms, 2),
                correlation_id=correlation_id,
            )

            # Warn on slow requests
            if duration_ms > self.slow_request_threshold_ms:
                logger.warning(
                    "Slow request detected",
                    path=request.url.path,
                    method=request.method,
                    duration_ms=round(duration_ms, 2),
                    threshold_ms=self.slow_request_threshold_ms,
                    correlation_id=correlation_id,
                )

            return response

        except Exception as exc:
            # Calculate duration for failed request
            duration_ms = (time.time() - start_time) * 1000

            # Log error with context
            logger.error(
                "Request failed with exception",
                path=request.url.path,
                method=request.method,
                duration_ms=round(duration_ms, 2),
                correlation_id=correlation_id,
                error_type=type(exc).__name__,
                error_message=str(exc),
                exc_info=True,
            )

            # Return error response
            return JSONResponse(
                status_code=500,
                content={
                    "detail": "Internal server error",
                    "correlation_id": correlation_id,
                },
                headers={
                    "X-Request-ID": correlation_id,
                    "X-Process-Time-Ms": f"{duration_ms:.2f}",
                }
            )


class RequestContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds request context to structlog context.

    This middleware ensures that all log statements within a request
    include the correlation_id for distributed tracing.

    Context Variables:
        - request_id: Unique request correlation ID
        - path: Request path
        - method: HTTP method
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Add request context to structlog and process request.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware or route handler

        Returns:
            HTTP response
        """
        # Get correlation ID from request state
        correlation_id = getattr(request.state, "request_id", "unknown")

        # Bind context variables to structlog for this request
        structlog.contextvars.bind_contextvars(
            request_id=correlation_id,
            path=request.url.path,
            method=request.method,
        )

        try:
            response = await call_next(request)
            return response
        finally:
            # Clear context variables after request completes
            structlog.contextvars.unbind_contextvars(
                "request_id", "path", "method"
            )


__all__ = ["MonitoringMiddleware", "RequestContextMiddleware"]
