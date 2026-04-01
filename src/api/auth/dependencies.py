"""
FastAPI dependencies for RBAC integration.

@MX:ANCHOR: FastAPI dependency injection for authorization
@MX:REASON: Reusable dependency pattern across all routes
@MX:SPEC: SPEC-PLATFORM-001 P2-T003
"""

import logging
from typing import Dict, Optional, Any
from fastapi import Depends, HTTPException, status, Header

from src.api.auth.rbac import RBACManager

logger = logging.getLogger(__name__)

# @MX:NOTE: Global RBAC manager instance, initialized lazily on first use
_rbac_manager: Optional[RBACManager] = None


def get_rbac_manager() -> RBACManager:
    """
    Get or create RBAC manager instance.

    Uses singleton pattern for efficiency.

    Returns:
        RBACManager instance
    """
    global _rbac_manager

    if _rbac_manager is None:
        # In production, this would come from config
        config = {
            "enabled": True,
            "default_role": "viewer",
            "roles": {
                "admin": {"permissions": ["*"], "inherits_from": []},
                "analyst": {
                    "permissions": [
                        "data:read",
                        "data:write",
                        "data:export",
                        "jobs:create",
                        "jobs:read",
                        "jobs:cancel",
                    ],
                    "inherits_from": ["viewer"],
                },
                "viewer": {"permissions": ["data:read", "jobs:read"], "inherits_from": []},
            },
        }
        _rbac_manager = RBACManager(config=config)
        logger.info("RBAC manager initialized with default configuration")

    return _rbac_manager


async def get_current_user_with_role(
    token_payload: Dict[str, Any],
    rbac: RBACManager = Depends(get_rbac_manager),
) -> Dict:
    """
    Get current user with role and permissions from JWT token.

    This dependency enriches the token payload with role permissions.

    Args:
        token_payload: JWT token payload containing user info
        rbac: RBAC manager instance

    Returns:
        User dictionary with id, username, role, and permissions
    """
    user_id = token_payload.get("sub")
    username = token_payload.get("username")
    role = token_payload.get("role", rbac.get_default_role())

    # Get all permissions for the role
    permissions = rbac.get_permissions(role)

    return {
        "id": int(user_id),
        "username": username,
        "role": role,
        "permissions": list(permissions),
    }


async def authorize_endpoint(
    user: Dict[str, Any],
    required_permission: str,
    rbac_manager: RBACManager = Depends(get_rbac_manager),
) -> None:
    """
    Authorize endpoint access based on required permission.

    Raises HTTPException(403) if user lacks required permission.

    Args:
        user: User dictionary with role and permissions
        required_permission: Required permission string
        rbac_manager: RBAC manager instance

    Raises:
        HTTPException: 403 Forbidden if permission not granted
    """
    user_role = user.get("role", rbac_manager.get_default_role())

    # Check if user has required permission
    if not rbac_manager.has_permission(user_role, required_permission):
        logger.warning(
            f"Authorization denied for user {user.get('id')}: "
            f"lacks permission '{required_permission}'"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission denied: {required_permission} required",
        )

    # Log successful authorization
    logger.debug(f"Authorization granted for user {user.get('id')}: {required_permission}")


async def get_current_user(
    authorization: Optional[str] = Header(None),
    rbac: RBACManager = Depends(get_rbac_manager),
) -> Dict[str, Any]:
    """
    Get current user from Authorization header.

    This is a simplified version that extracts user info from a mock token.
    In production, this would validate a JWT token and extract the payload.

    Args:
        authorization: Authorization header value (format: "Bearer token")
        rbac: RBAC manager instance

    Returns:
        User dictionary with id, username, role, and permissions
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    # Extract token from "Bearer <token>" format
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication format",
        )

    token = authorization[7:]  # Remove "Bearer " prefix

    # For testing, decode the mock token (format: "user_id:username:role")
    try:
        user_id, username, role = token.split(":")
        user_info = {
            "sub": user_id,
            "username": username,
            "role": role,
        }
        return await get_current_user_with_role(user_info, rbac)
    except Exception as e:
        logger.error(f"Failed to decode token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )


async def get_db():
    """
    Get database session.

    This is a placeholder for database session management.
    In production, this would return an async database session.

    Yields:
        Database session
    """
    # Placeholder: return None for now
    # In production, this would use SQLAlchemy async session
    yield None
