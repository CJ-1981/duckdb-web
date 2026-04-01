"""
FastAPI Application Main module

Creates the main FastAPI application instance with middleware stack,
 routers, and lifecycle events, and OpenAPI documentation.
"""

import logging
from typing import Optional
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from src.core.config.loader import Config
from src.api.dependencies import get_processor, get_config
from src.api.middleware import (
    RequestIDMiddleware,
    LoggingMiddleware,
    ErrorHandlerMiddleware
)
from src.api.routes.system import router as health_router
from src.api.routes.users import router as users_router
from src.api.routes.data import router as data_router
from src.api.routes.workflows import router as workflows_router
from src.api.routes.jobs import router as jobs_router


# Configure logging
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create FastAPI application instance"""
    app = FastAPI(
        title="DuckDB Data Processor API",
        version="1.0.0",
        description="Full-stack data analysis platform powered by DuckDB",
        docs_url="/docs",
        redoc_url="/redoc"
    )

    # Load configuration
    config = next(get_config())
    app_config = config

    # Configure CORS middleware
    # @MX:NOTE: CORS must to be configured from config
    # Default CORS settings - will be overridden by config
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add custom middleware stack
    # Note: Order matters - outer to inner
    # 1. CORS (first) - already added above
    # 2. Request ID
    app.add_middleware(RequestIDMiddleware)
    # 3. Logging
    app.add_middleware(LoggingMiddleware)
    # 4. Error Handler
    app.add_middleware(ErrorHandlerMiddleware)
    # 5. Authentication (will be added in later task)

    # Register routers
    # Note: Additional routers will be added in later tasks (auth, jobs, etc.)
    app.include_router(health_router)    # System configuration endpoints
    app.include_router(users_router)     # User management endpoints
    app.include_router(data_router)      # Data processing endpoints
    app.include_router(workflows_router) # Workflow management endpoints
    app.include_router(jobs_router)      # Job execution endpoints

    # Lifecycle events
    @app.on_event("startup")
    async def startup_event():
        """Initialize application state on startup"""
        logger.info("Starting DuckDB Data Processor API...")

        logger.info(f"Configuration loaded from {app_config._config_path}")

        # Initialize processor singleton
        processor = next(get_processor())
        app.state.processor = processor
        logger.info("Processor initialized")

    @app.on_event("shutdown")
    async def shutdown_event():
        """Cleanup application state on shutdown"""
        logger.info("Shutting down DuckDB Data Processor API...")

        # Close processor if exists
        processor = app.state.processor
        if processor:
            processor.close()

        logger.info("Application shutdown complete")

    # Root endpoints
    @app.get("/")
    async def root():
        """Root endpoint returning API information"""
        return {
            "message": "DuckDB Data Processor API",
            "version": "1.0.0",
            "documentation": "/docs"
        }

    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return {"status": "healthy"}

    return app
