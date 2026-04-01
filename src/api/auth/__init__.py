"""
Authentication and authorization module.

@MX:NOTE: Provides RBAC, JWT, and authorization utilities
"""

from src.api.auth.rbac import RBACManager
from src.api.auth.models import Role, Permission, UserRole, RBACConfig
from src.api.auth.permissions import (
    DATA_READ,
    DATA_WRITE,
    DATA_DELETE,
    DATA_EXPORT,
    JOBS_CREATE,
    JOBS_READ,
    JOBS_CANCEL,
    USERS_MANAGE,
    SYSTEM_CONFIG,
)
from src.api.auth.decorators import require_role, require_permission
from src.api.auth.dependencies import (
    get_rbac_manager,
    get_current_user_with_role,
    authorize_endpoint,
)

