"""
FastAPI Application Main module

Creates the main FastAPI application instance with middleware stack,
 routers, and lifecycle events, and OpenAPI documentation.
"""

import logging
import os
import sys
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
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
from src.csv_parser.api import router as csv_router


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
    # @MX:NOTE: CORS configured for Vercel frontend + local backend development
    # Default CORS settings - will be overridden by config
    cors_origins = [
        "http://localhost:3000",        # Local Next.js development
        "http://127.0.0.1:3000",         # Alternative local development
        "http://localhost:3001",        # E2E test server
        "http://127.0.0.1:3001",         # E2E test server alternative
        "http://localhost:3002",        # Alternative dev server
        "http://127.0.0.1:3002",         # Alternative dev server alternative
        "http://localhost:19006",       # Vercel dev server
        os.getenv("VERCEL_URL", ""),     # Dynamic Vercel deployment URL
        # Add your Vercel deployment URL here:
        # "https://your-app.vercel.app",
    ]

    # Filter out empty strings
    cors_origins = [origin for origin in cors_origins if origin]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins if cors_origins else ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Ensure all error responses include CORS headers so browser can read them
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={"detail": exc.errors()},
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": str(exc)},
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
    app.include_router(csv_router)       # CSV upload and processing endpoints

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
    @app.get("/api/health")
    async def health_check():
        """Health check endpoint"""
        return {"status": "healthy"}

    # Handle static files for bundled application
    # We check multiple possible locations for the 'out' directory
    # 1. Current working directory
    # 2. Bundled application directory (PyInstaller sys._MEIPASS)
    
    base_path = Path(getattr(sys, '_MEIPASS', os.getcwd()))
    frontend_path = base_path / "out"

    if frontend_path.exists() and frontend_path.is_dir():
        logger.info(f"Serving static frontend from {frontend_path}")
        
        # Mount the static files (images, JS, CSS)
        # Note: Next.js static export puts assets in _next
        app.mount("/_next", StaticFiles(directory=str(frontend_path / "_next")), name="next-static")
        
        # Serve index.html for the root and catch-all
        @app.get("/{full_path:path}")
        async def serve_frontend(full_path: str):
            # If it's an API route that wasn't caught, or a health check, don't serve index.html
            if full_path.startswith("api/"):
                return JSONResponse(status_code=404, content={"detail": "API endpoint not found"})
            
            # Check if requested file exists in 'out' folder
            requested_file = frontend_path / full_path
            if requested_file.exists() and requested_file.is_file():
                return FileResponse(str(requested_file))
            
            # Default to index.html for SPAs
            return FileResponse(str(frontend_path / "index.html"))
    else:
        logger.warning(f"Frontend directory not found at {frontend_path}. API only mode.")
        @app.get("/")
        async def root():
            """Root endpoint returning API information"""
            return {
                "message": "DuckDB Data Processor API",
                "version": "1.0.0",
                "documentation": "/docs"
            }

    return app


# Module-level app instance for import by tests and other modules
app = create_app()

if __name__ == "__main__":
    import uvicorn
    import webbrowser
    from threading import Timer

    # Load port from config or default
    port = 8000
    try:
        config = next(get_config())
        port = getattr(config.api, 'port', 8000)
    except:
        pass

    # Open browser automatically
    def open_browser():
        webbrowser.open(f"http://localhost:{port}")

    Timer(1.5, open_browser).start()
    
    # Run uvicorn
    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=port)
