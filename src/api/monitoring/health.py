"""
Health Check Endpoints

Kubernetes-style health probes for container orchestration:
- /health/live - Liveness probe (app is running)
- /health/ready - Readiness probe (can serve traffic, checks dependencies)
- /health/startup - Startup probe (initialization complete)

These endpoints follow standard Kubernetes probe patterns and are
designed for integration with container orchestrators.

Reference:
    https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/
"""

from typing import Dict, Any
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from src.api.monitoring.logging_config import get_logger
from src.api.dependencies import get_processor, get_config


# Module logger
logger = get_logger(__name__)

# Create router
router = APIRouter(prefix="/health", tags=["health"])


class HealthResponse(BaseModel):
    """Standard health check response format."""
    status: str = Field(..., description="Health status: healthy, unhealthy, or ready")
    timestamp: str = Field(..., description="ISO 8601 timestamp")
    version: str = Field(default="1.0.0", description="Application version")


class ReadinessResponse(BaseModel):
    """Extended readiness check with dependency status."""
    status: str = Field(..., description="Readiness status: ready or not_ready")
    timestamp: str = Field(..., description="ISO 8601 timestamp")
    checks: Dict[str, Any] = Field(..., description="Dependency health checks")


@router.get("/live", response_model=HealthResponse)
async def liveness_probe() -> HealthResponse:
    """
    Liveness probe - checks if the application is running.

    Kubernetes uses this probe to know when to restart a container.
    If this probe fails, the container is restarted.

    Returns:
        HealthResponse with current status

    HTTP Status Codes:
        200: Application is alive
        503: Application is dead (should never happen if code runs)
    """
    logger.debug("Liveness probe check")

    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(timezone.utc).isoformat(),
        version="1.0.0"
    )


@router.get("/ready", response_model=ReadinessResponse)
async def readiness_probe(
    processor = Depends(get_processor),
    config = Depends(get_config)
) -> ReadinessResponse:
    """
    Readiness probe - checks if the application can serve traffic.

    Kubernetes uses this probe to know when a container is ready
    to start accepting traffic. If this probe fails, the container
    is removed from service endpoints.

    Checks:
    - Configuration loaded
    - DuckDB processor initialized
    - Database connections (if configured)

    Returns:
        ReadinessResponse with detailed dependency status

    HTTP Status Codes:
        200: Application is ready
        503: Application is not ready (dependencies unhealthy)
    """
    logger.debug("Readiness probe check")

    checks: Dict[str, Any] = {}

    # Check 1: Configuration
    checks["config"] = {
        "status": "ok" if config else "missing",
        "description": "Configuration loaded" if config else "Configuration not loaded"
    }

    # Check 2: DuckDB Processor
    try:
        if processor:
            # Try to execute a simple DuckDB query
            processor.execute_query("SELECT 1 as test")
            checks["processor"] = {
                "status": "ok",
                "description": "DuckDB processor operational"
            }
        else:
            checks["processor"] = {
                "status": "error",
                "description": "DuckDB processor not initialized"
            }
    except Exception as exc:
        logger.error("Processor health check failed", error=str(exc))
        checks["processor"] = {
            "status": "error",
            "description": f"DuckDB processor error: {str(exc)}"
        }

    # Check 3: Database connections (if configured)
    checks["database"] = {
        "status": "ok",
        "description": "No external database configured"
    }

    # Determine overall readiness
    all_healthy = all(
        check.get("status") == "ok"
        for check in checks.values()
    )

    readiness_status = "ready" if all_healthy else "not_ready"

    if not all_healthy:
        logger.warning(
            "Readiness check failed",
            checks=checks,
            status=readiness_status
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": readiness_status,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "checks": checks
            }
        )

    return ReadinessResponse(
        status=readiness_status,
        timestamp=datetime.now(timezone.utc).isoformat(),
        checks=checks
    )


@router.get("/startup", response_model=HealthResponse)
async def startup_probe(
    processor = Depends(get_processor)
) -> HealthResponse:
    """
    Startup probe - checks if application initialization is complete.

    Kubernetes uses this probe to know when a container has started.
    If this probe fails, the container is restarted but with an
    exponential backoff delay.

    This probe is particularly useful for applications with slow
    initialization times (e.g., loading large data files).

    Returns:
        HealthResponse with current status

    HTTP Status Codes:
        200: Application has started successfully
        503: Application has not finished starting
    """
    logger.debug("Startup probe check")

    # Check if processor is initialized
    if not processor:
        logger.warning("Startup probe failed: processor not initialized")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "starting",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "description": "Application initialization incomplete"
            }
        )

    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(timezone.utc).isoformat(),
        version="1.0.0"
    )


__all__ = ["router"]
