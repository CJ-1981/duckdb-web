"""
Metrics Endpoint

Prometheus metrics exposition endpoint for scraping.
Exposes metrics in Prometheus text format.

Reference:
    https://prometheus.io/docs/instrumenting/exposition_formats/
"""

from os import getenv
from typing import Any

from fastapi import APIRouter, Response
from starlette.responses import PlainTextResponse

from src.api.monitoring.logging_config import get_logger

# Try to import prometheus_client utilities
try:
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    CONTENT_TYPE_LATEST = "text/plain"

    def _generate_latest_stub(__registry: Any) -> bytes:  # type: ignore[misc]
        """Stub function when prometheus_client is not available."""
        return b""

    # Use stub when prometheus_client is not available
    generate_latest = _generate_latest_stub  # type: ignore[misc]


# Module logger
logger = get_logger(__name__)

# Create router
router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("", include_in_schema=False)
async def metrics_endpoint() -> Response:
    """
    Prometheus metrics exposition endpoint.

    Returns metrics in Prometheus text format for scraping.
    Only available if prometheus_client is installed.

    HTTP Status Codes:
        200: Metrics successfully generated
        503: Prometheus client not available

    Configuration:
        Set PROMETHEUS_ENABLED=true to enable this endpoint

    Example Prometheus Configuration:
        scrape_configs:
          - job_name: 'duckdb-processor'
            metrics_path: /metrics
            static_configs:
              - targets: ['localhost:8000']
    """
    if not PROMETHEUS_AVAILABLE:
        logger.warning("Metrics endpoint requested but Prometheus client not installed")
        return PlainTextResponse(
            content="# Prometheus client not available. Install prometheus-client package.",
            status_code=503
        )

    # Check if metrics are enabled
    if not getenv("PROMETHEUS_ENABLED", "false").lower() == "true":
        logger.warning("Metrics endpoint requested but PROMETHEUS_ENABLED is false")
        return PlainTextResponse(
            content="# Metrics disabled. Set PROMETHEUS_ENABLED=true to enable.",
            status_code=503
        )

    # Generate metrics in Prometheus format
    if not PROMETHEUS_AVAILABLE:
        logger.error("generate_latest not available - Prometheus client not properly initialized")
        return PlainTextResponse(
            content="# Prometheus client initialization error.",
            status_code=503
        )

    from prometheus_client import REGISTRY

    metrics_data = generate_latest(REGISTRY)

    logger.debug("Metrics scraped")

    return Response(
        content=metrics_data,
        media_type=CONTENT_TYPE_LATEST,
        headers={
            "Content-Type": CONTENT_TYPE_LATEST,
        }
    )


__all__ = ["router"]
