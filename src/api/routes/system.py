"""
System configuration API routes with RBAC authorization.

@MX:NOTE: Example routes demonstrating RBAC integration (admin-only)
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from src.api.auth.decorators import require_role
from src.api.auth.dependencies import get_current_user_with_role


router = APIRouter(prefix="/api/v1/system", tags=["System"])


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str
    backend: str
    version: str


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint for testing and monitoring.

    Returns:
        Health status with backend and version info
    """
    return HealthResponse(
        status="healthy",
        backend="FastAPI",
        version="1.0.0",
    )


class SystemConfigResponse(BaseModel):
    """System configuration response model."""

    config: Dict[str, Any]
    version: str


@router.get("/config", response_model=SystemConfigResponse)
@require_role("admin")
async def get_config(
    current_user: Dict = Depends(get_current_user_with_role),
):
    """
    Get system configuration (admin only).

    Args:
        current_user: Current user with role

    Returns:
        System configuration
    """
    # Mock config data
    config = {
        "config": {
            "auth": {"enabled": True},
            "database": {"pool_size": 10},
        },
        "version": "1.0.0",
    }
    return SystemConfigResponse(**config)
