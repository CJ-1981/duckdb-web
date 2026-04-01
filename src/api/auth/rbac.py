"""
Role-Based Access Control (RBAC) manager implementation.

@MX:ANCHOR: Core RBAC authorization logic
@MX:REASON: Central authorization check for all API endpoints
@MX:SPEC: SPEC-PLATFORM-001 P2-T003
"""

from typing import Dict, List, Set, Optional, Any
from collections import defaultdict
import logging

from src.api.auth.models import Role, RoleConfig, RBACConfig

logger = logging.getLogger(__name__)


class RBACManager:
    """
    Manages role-based access control with role hierarchy and permission checking.

    @MX:NOTE: Supports role inheritance, wildcard permissions for admin role, and default role fallback
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize RBAC manager with configuration.

        Args:
            config: RBAC configuration dictionary containing:
                - enabled: bool - Enable/disable RBAC
                - default_role: str - Default role for new users
                - roles: dict - Role definitions mapping
        """
        self.config = config
        self.enabled = config.get("enabled", True)
        self.default_role = config.get("default_role", "viewer")

        # Build role registry
        self.roles: Dict[str, Role] = {}
        self.role_inheritance: Dict[str, List[str]] = defaultdict(list)

        # Initialize roles from config
        roles_config = config.get("roles", {})
        for role_name, role_data in roles_config.items():
                role = Role(
                    name=role_name,
                    permissions=role_data.get("permissions", []),
                    inherits_from=role_data.get("inherits_from", []),
                )
                self.roles[role_name] = role

                # Build inheritance graph
                if role.inherits_from:
                    self.role_inheritance[role_name] = role.inherits_from

        # Build permission cache for performance
        self._permission_cache: Dict[str, Set[str]] = {}

    def get_permissions(self, role_name: Optional[str]) -> Set[str]:
        """
        Get all permissions for a role, including inherited permissions.

        Args:
            role_name: Role name to get permissions for

        Returns:
            Set of permission strings
        """
        if not role_name or role_name not in self.roles:
            # Default to viewer role for unknown roles
            role_name = self.default_role

        # Check cache first
        if role_name in self._permission_cache:
            return self._permission_cache[role_name]

        permissions = set()
        visited_roles = set()
        roles_to_visit = [role_name]

        # Traverse role hierarchy to collect all permissions
        while roles_to_visit:
            current_role = roles_to_visit.pop(0)

            # Skip if already visited (prevents infinite loops)
            if current_role in visited_roles:
                continue

            visited_roles.add(current_role)

            # Get role definition
            if current_role in self.roles:
                role = self.roles[current_role]

                # Add direct permissions
                permissions.update(role.permissions)

                # Add inherited roles to visit list
                if current_role in self.role_inheritance:
                    for parent_role in self.role_inheritance[current_role]:
                        if parent_role not in visited_roles:
                            roles_to_visit.append(parent_role)

        # Cache the result
        self._permission_cache[role_name] = permissions

        return permissions

    def has_permission(self, role_name: Optional[str], permission: str) -> bool:
        """
        Check if a role has a specific permission.

        Args:
            role_name: Role name to check
            permission: Permission string to check (e.g., "data:read")

        Returns:
            True if role has permission, False otherwise
        """
        permissions = self.get_permissions(role_name)

        # Check for wildcard permission (admin has all permissions)
        if "*" in permissions:
            return True

        return permission in permissions

    def has_role(self, user_role: Optional[str], required_roles: List[str]) -> bool:
        """
        Check if user has any of the required roles.

        Args:
            user_role: User's current role
            required_roles: List of acceptable roles

        Returns:
            True if user has any required role, False otherwise
        """
        if not user_role:
            user_role = self.default_role

        return user_role in required_roles

    def get_inherited_roles(self, role_name: Optional[str]) -> Set[str]:
        """
        Get all roles inherited by a role (direct and transitive).

        Args:
            role_name: Role name to get inherited roles for

        Returns:
            Set of inherited role names
        """
        if not role_name or role_name not in self.roles:
            return set()

        inherited_roles = set()
        roles_to_visit = [role_name]
        visited = set()

        while roles_to_visit:
            current = roles_to_visit.pop(0)

            if current in visited:
                continue

            visited.add(current)

            if current in self.role_inheritance:
                for parent in self.role_inheritance[current]:
                    if parent not in visited and parent in self.roles:
                        roles_to_visit.append(parent)
                        inherited_roles.add(parent)

        return inherited_roles

    def get_default_role(self) -> str:
        """
        Get the default role for new users.

        Returns:
            Default role name
        """
        return self.default_role

    def is_enabled(self) -> bool:
        """
        Check if RBAC is enabled.

        Returns:
            True if RBAC is enabled, False otherwise
        """
        return self.enabled
