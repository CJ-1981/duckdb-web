"""
Middleware Package

Provides middleware components for FastAPI application:
- RequestIDMiddleware: Adds unique request ID to each request
- LoggingMiddleware: Logs request/response information
- ErrorHandlerMiddleware: Catches and formats errors consistently
"""

import uuid
import time
import logging
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


logger = logging.getLogger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds a unique request ID to each request.

    The request ID is added to:
    - Request state (request.state.request_id)
    - Response headers (X-Request-ID)
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate unique request ID
        request_id = str(uuid.uuid4())

        # Store in request state
        request.state.request_id = request_id

        # Call next middleware/handler
        response = await call_next(request)

        # Add to response headers
        response.headers["X-Request-ID"] = request_id

        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that logs request and response information.

    Logs:
    - Request method, path, and request ID
    - Response status code and duration
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Get request ID (set by RequestIDMiddleware)
        request_id = getattr(request.state, "request_id", "unknown")

        # Log request
        logger.info(
            f"Request started: {request.method} {request.url.path} "
            f"[Request-ID: {request_id}]"
        )

        # Track timing
        start_time = time.time()

        # Call next middleware/handler
        response = await call_next(request)

        # Calculate duration
        duration = time.time() - start_time

        # Log response
        logger.info(
            f"Request completed: {request.method} {request.url.path} "
            f"- {response.status_code} ({duration:.3f}s) "
            f"[Request-ID: {request_id}]"
        )

        return response


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """
    Middleware that catches unhandled exceptions and returns JSON errors.

    Ensures consistent error response format:
    {
    "detail": "Error message",
    "request_id": "uuid"
    }
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            # Call next middleware/handler
            response = await call_next(request)
            return response

        except Exception as e:
            # Log the error
            request_id = getattr(request.state, "request_id", "unknown")
            logger.error(
                f"Unhandled exception: {str(e)} "
                f"[Request-ID: {request_id}]",
                exc_info=True
            )

            # Return JSON error response - include CORS headers so browser can read the error
            return JSONResponse(
                status_code=500,
                content={
                    "detail": "Internal server error",
                    "request_id": request_id
                },
                headers={
                    "X-Request-ID": request_id,
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "DELETE, GET, HEAD, OPTIONS, PATCH, POST, PUT",
                    "Access-Control-Allow-Headers": "content-type, authorization",
                }
            )


__all__ = ["RequestIDMiddleware", "LoggingMiddleware", "ErrorHandlerMiddleware"]
