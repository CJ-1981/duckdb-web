"""
Authorization decorators for FastAPI endpoints.

@MX:ANCHOR: Authorization decorators used across all API routes
@MX:REASON: Centralized authorization logic for consistent security enforcement
@MX:SPEC: SPEC-PLATFORM-001 P2-T003
@MX:NOTE: Decorators are pass-through for now; authorization happens in endpoint functions
"""

from functools import wraps
from typing import Callable, List, Optional
from fastapi import HTTPException, status, Depends

import logging

logger = logging.getLogger(__name__)


def require_role(*roles: str):
    """
    Decorator to require specific role(s) for endpoint access.

    User must have ANY of the specified roles to access the endpoint.

    Args:
        *roles: Required role names (any one is sufficient)

    Usage:
        @require_role("admin")
        async def admin_only_endpoint(...):
            pass
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            if current_user:
                user_role = current_user.get('role', '') if isinstance(current_user, dict) else getattr(current_user, 'role', '')
                if user_role not in roles:
                    user_id = current_user.get('id') if isinstance(current_user, dict) else getattr(current_user, 'id', None)
                    username = current_user.get('username') if isinstance(current_user, dict) else getattr(current_user, 'username', None)
                    log_authorization(
                        user_id=user_id,
                        username=username,
                        permission=f"role:{','.join(roles)}",
                        granted=False,
                        reason=f"Role '{user_role}' not in required roles"
                    )
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Role '{', '.join(roles)}' required"
                    )
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_permission(*permissions: str):
    """
    Decorator to require specific permission(s) for endpoint access.

    User must have ALL of the specified permissions to access the endpoint.

    Args:
        *permissions: Required permission strings (all are required)

    Usage:
        @require_permission("data:read")
        async def read_data_endpoint(current_user: dict = Depends(get_current_user)):
            pass
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            if current_user:
                from src.api.auth.dependencies import get_rbac_manager
                rbac = get_rbac_manager()
                user_role = current_user.get('role', '') if isinstance(current_user, dict) else getattr(current_user, 'role', '')
                user_id = current_user.get('id') if isinstance(current_user, dict) else getattr(current_user, 'id', None)
                username = current_user.get('username') if isinstance(current_user, dict) else getattr(current_user, 'username', None)

                for perm in permissions:
                    if not rbac.has_permission(user_role, perm):
                        log_authorization(
                            user_id=user_id,
                            username=username,
                            permission=perm,
                            granted=False,
                            reason=f"Role '{user_role}' lacks permission '{perm}'"
                        )
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail=f"Permission '{perm}' required"
                        )

                # Log successful authorization
                for perm in permissions:
                    log_authorization(
                        user_id=user_id,
                        username=username,
                        permission=perm,
                        granted=True
                    )
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def log_authorization(
    user_id: Optional[int],
    username: Optional[str],
    permission: str,
    granted: bool,
    reason: Optional[str] = None,
) -> None:
    """
    Log authorization attempt for audit trail.

    @MX:NOTE: All authorization attempts are logged for security auditing

    Args:
        user_id: User ID attempting access
        username: Username attempting access
        permission: Permission or role being checked
        granted: True if access granted, False if denied
        reason: Optional reason for the decision
    """
    from datetime import datetime

    log_entry = {
        "user_id": user_id,
        "username": username,
        "permission": permission,
        "granted": granted,
        "reason": reason,
        "timestamp": datetime.utcnow().isoformat(),
    }

    if granted:
        logger.info(f"Authorization GRANTED: user={username}, permission={permission}")
    else:
        logger.warning(
            f"Authorization DENIED: user={username}, permission={permission}, reason={reason}"
        )

    # In production, this would be written to audit log database
    # For now, we just log it
    # TODO: Implement audit log persistence (SPEC-PLATFORM-001 UR-002)
