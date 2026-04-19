"""
Comprehensive test suite for Role-Based Access Control (RBAC) following TDD methodology.

Tests are designed to document expected behavior before implementation.
All tests should FAIL initially (RED phase), then pass after implementation (GREEN phase).
"""

import pytest
from datetime import datetime
from typing import List, Set, Dict, Any
from unittest.mock import Mock, patch, MagicMock
from pydantic import BaseModel, Field


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def rbac_config():
    """Create RBAC configuration with role hierarchy."""
    return {
        "enabled": True,
        "default_role": "viewer",
        "roles": {
            "admin": {
                "permissions": ["*"],
                "inherits_from": [],
            },
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
            "viewer": {
                "permissions": ["data:read", "jobs:read"],
                "inherits_from": [],
            },
        },
    }


@pytest.fixture
def mock_rbac_manager(rbac_config):
    """Create RBAC manager instance for testing."""
    from src.api.auth.rbac import RBACManager

    manager = RBACManager(config=rbac_config)
    return manager


@pytest.fixture
def admin_user():
    """Create admin user for testing."""
    return {
        "id": 1,
        "username": "admin",
        "email": "admin@example.com",
        "role": "admin",
        "created_at": datetime(2024, 1, 1, 12, 0, 0),
    }


@pytest.fixture
def analyst_user():
    """Create analyst user for testing."""
    return {
        "id": 2,
        "username": "analyst",
        "email": "analyst@example.com",
        "role": "analyst",
        "created_at": datetime(2024, 1, 1, 12, 0, 0),
    }


@pytest.fixture
def viewer_user():
    """Create viewer user for testing."""
    return {
        "id": 3,
        "username": "viewer",
        "email": "viewer@example.com",
        "role": "viewer",
        "created_at": datetime(2024, 1, 1, 12, 0, 0),
    }


# ============================================================================
# Role Model Tests
# ============================================================================


class TestRoleModels:
    """Test role and permission models."""

    def test_role_model_creation(self):
        """Test creating a role with permissions."""
        from src.api.auth.models import Role

        role = Role(
            name="analyst",
            permissions=["data:read", "data:write"],
            inherits_from=["viewer"],
        )

        assert role.name == "analyst"
        assert "data:read" in role.permissions
        assert "data:write" in role.permissions
        assert "viewer" in role.inherits_from

    def test_permission_model_creation(self):
        """Test creating a permission model."""
        from src.api.auth.models import Permission

        permission = Permission(
            name="data:read",
            resource="data",
            action="read",
            description="Read access to datasets",
        )

        assert permission.name == "data:read"
        assert permission.resource == "data"
        assert permission.action == "read"
        assert permission.description == "Read access to datasets"

    def test_user_role_model_creation(self):
        """Test creating a user role assignment."""
        from src.api.auth.models import UserRole

        user_role = UserRole(
            user_id=1,
            role_name="analyst",
            assigned_at=datetime(2024, 1, 1, 12, 0, 0),
            assigned_by=2,
        )

        assert user_role.user_id == 1
        assert user_role.role_name == "analyst"
        assert user_role.assigned_at == datetime(2024, 1, 1, 12, 0, 0)
        assert user_role.assigned_by == 2


# ============================================================================
# RBAC Manager Tests
# ============================================================================


class TestRBACManager:
    """Test RBAC manager functionality."""

    def test_rbac_manager_initialization(self, rbac_config):
        """Test RBAC manager initialization."""
        from src.api.auth.rbac import RBACManager

        manager = RBACManager(config=rbac_config)

        assert manager is not None
        assert manager.default_role == "viewer"
        assert len(manager.roles) == 3
        assert "admin" in manager.roles
        assert "analyst" in manager.roles
        assert "viewer" in manager.roles

    def test_get_permissions_for_admin(self, mock_rbac_manager, admin_user):
        """Test getting all permissions for admin role (wildcard)."""
        permissions = mock_rbac_manager.get_permissions("admin")

        # Admin should have all permissions (wildcard)
        assert "*" in permissions
        assert len(permissions) >= 1  # At least wildcard

    def test_get_permissions_for_analyst(self, mock_rbac_manager, analyst_user):
        """Test getting permissions for analyst role with inheritance."""
        permissions = mock_rbac_manager.get_permissions("analyst")

        # Analyst should have its own permissions
        assert "data:read" in permissions
        assert "data:write" in permissions
        assert "data:export" in permissions
        assert "jobs:create" in permissions
        assert "jobs:read" in permissions
        assert "jobs:cancel" in permissions

        # Plus inherited viewer permissions
        # Note: data:read and jobs:read are duplicated, but set handles uniqueness

    def test_get_permissions_for_viewer(self, mock_rbac_manager, viewer_user):
        """Test getting permissions for viewer role."""
        permissions = mock_rbac_manager.get_permissions("viewer")

        # Viewer should have only read permissions
        assert "data:read" in permissions
        assert "jobs:read" in permissions
        assert "data:write" not in permissions
        assert "data:delete" not in permissions
        assert "jobs:create" not in permissions

    def test_role_inheritance_chain(self, mock_rbac_manager):
        """Test role inheritance chain resolution."""
        # Analyst inherits from viewer
        inherited_roles = mock_rbac_manager.get_inherited_roles("analyst")

        assert "viewer" in inherited_roles

        # Viewer has no inheritance
        inherited_roles = mock_rbac_manager.get_inherited_roles("viewer")

        assert len(inherited_roles) == 0

    def test_has_permission_admin(self, mock_rbac_manager, admin_user):
        """Test admin has all permissions via wildcard."""
        # Admin should have any permission checked
        assert mock_rbac_manager.has_permission("admin", "data:read") is True
        assert mock_rbac_manager.has_permission("admin", "data:write") is True
        assert mock_rbac_manager.has_permission("admin", "data:delete") is True
        assert mock_rbac_manager.has_permission("admin", "users:manage") is True
        assert mock_rbac_manager.has_permission("admin", "system:config") is True
        assert mock_rbac_manager.has_permission("admin", "any:permission") is True

    def test_has_permission_analyst(self, mock_rbac_manager, analyst_user):
        """Test analyst has appropriate permissions."""
        # Analyst should have data and jobs permissions
        assert mock_rbac_manager.has_permission("analyst", "data:read") is True
        assert mock_rbac_manager.has_permission("analyst", "data:write") is True
        assert mock_rbac_manager.has_permission("analyst", "data:export") is True
        assert mock_rbac_manager.has_permission("analyst", "jobs:create") is True
        assert mock_rbac_manager.has_permission("analyst", "jobs:read") is True
        assert mock_rbac_manager.has_permission("analyst", "jobs:cancel") is True

        # Analyst should NOT have admin-only permissions
        assert mock_rbac_manager.has_permission("analyst", "users:manage") is False
        assert mock_rbac_manager.has_permission("analyst", "system:config") is False
        assert mock_rbac_manager.has_permission("analyst", "data:delete") is False

    def test_has_permission_viewer(self, mock_rbac_manager, viewer_user):
        """Test viewer has read-only permissions."""
        # Viewer should have read permissions
        assert mock_rbac_manager.has_permission("viewer", "data:read") is True
        assert mock_rbac_manager.has_permission("viewer", "jobs:read") is True

        # Viewer should NOT have write or admin permissions
        assert mock_rbac_manager.has_permission("viewer", "data:write") is False
        assert mock_rbac_manager.has_permission("viewer", "data:delete") is False
        assert mock_rbac_manager.has_permission("viewer", "jobs:create") is False
        assert mock_rbac_manager.has_permission("viewer", "users:manage") is False

    def test_has_role_single(self, mock_rbac_manager):
        """Test checking if user has a specific role."""
        assert mock_rbac_manager.has_role("admin", ["admin"]) is True
        assert mock_rbac_manager.has_role("analyst", ["analyst"]) is True
        assert mock_rbac_manager.has_role("viewer", ["viewer"]) is True

        # Negative cases
        assert mock_rbac_manager.has_role("analyst", ["admin"]) is False
        assert mock_rbac_manager.has_role("viewer", ["analyst", "admin"]) is False

    def test_has_role_multiple(self, mock_rbac_manager):
        """Test checking if user has any of multiple roles."""
        # Should pass if user has any of the required roles
        assert mock_rbac_manager.has_role("admin", ["admin", "analyst"]) is True
        assert mock_rbac_manager.has_role("analyst", ["admin", "analyst"]) is True
        assert mock_rbac_manager.has_role("analyst", ["analyst", "viewer"]) is True

    def test_get_default_role(self, mock_rbac_manager):
        """Test getting default role for new users."""
        default_role = mock_rbac_manager.get_default_role()

        assert default_role == "viewer"

    def test_role_hierarchy_respected(self, mock_rbac_manager):
        """Test that role hierarchy is properly respected."""
        # Admin > Analyst > Viewer
        # Admin should have all permissions
        admin_perms = mock_rbac_manager.get_permissions("admin")
        analyst_perms = mock_rbac_manager.get_permissions("analyst")
        viewer_perms = mock_rbac_manager.get_permissions("viewer")

        # Analyst should have all viewer permissions
        for perm in viewer_perms:
            assert perm in analyst_perms or "*" in analyst_perms

        # Admin should have wildcard (effectively all permissions)
        assert "*" in admin_perms


# ============================================================================
# Authorization Decorator Tests
# ============================================================================


class TestAuthorizationDecorators:
    """Test authorization decorators."""

    @pytest.mark.asyncio
    async def test_require_role_decorator_success(self, mock_rbac_manager, admin_user):
        """Test require_role decorator with authorized user."""
        from src.api.auth.decorators import require_role
        from fastapi import HTTPException

        @require_role("admin")
        async def protected_endpoint(current_user: dict = None):
            return {"status": "success", "user": current_user}

        # Should not raise exception for admin
        result = await protected_endpoint(current_user=admin_user)

        assert result["status"] == "success"
        assert result["user"] == admin_user

    @pytest.mark.asyncio
    async def test_require_role_decorator_failure(self, mock_rbac_manager, viewer_user):
        """Test require_role decorator with unauthorized user."""
        from src.api.auth.decorators import require_role
        from fastapi import HTTPException

        @require_role("admin")
        async def protected_endpoint(current_user: dict = None):
            return {"status": "success"}

        # Should raise HTTPException with 403 status
        with pytest.raises(HTTPException) as exc_info:
            await protected_endpoint(current_user=viewer_user)

        assert exc_info.value.status_code == 403
        assert "admin" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_require_role_multiple_any(self, mock_rbac_manager, analyst_user):
        """Test require_role decorator with multiple roles (any match)."""
        from src.api.auth.decorators import require_role

        @require_role("admin", "analyst")
        async def protected_endpoint(current_user: dict = None):
            return {"status": "success"}

        # Should pass for analyst (any of the roles)
        result = await protected_endpoint(current_user=analyst_user)

        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_require_permission_decorator_success(self, mock_rbac_manager, analyst_user):
        """Test require_permission decorator with authorized user."""
        from src.api.auth.decorators import require_permission

        @require_permission("data:write")
        async def protected_endpoint(current_user: dict = None):
            return {"status": "success"}

        # Should not raise exception for analyst with data:write permission
        result = await protected_endpoint(current_user=analyst_user)

        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_require_permission_decorator_failure(self, mock_rbac_manager, viewer_user):
        """Test require_permission decorator with unauthorized user."""
        from src.api.auth.decorators import require_permission
        from fastapi import HTTPException

        @require_permission("data:write")
        async def protected_endpoint(current_user: dict = None):
            return {"status": "success"}

        # Should raise HTTPException with 403 status
        with pytest.raises(HTTPException) as exc_info:
            await protected_endpoint(current_user=viewer_user)

        assert exc_info.value.status_code == 403
        assert "data:write" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_require_permission_multiple_all(self, mock_rbac_manager, analyst_user):
        """Test require_permission decorator with multiple permissions (all required)."""
        from src.api.auth.decorators import require_permission

        @require_permission("data:read", "data:write")
        async def protected_endpoint(current_user: dict = None):
            return {"status": "success"}

        # Should pass for analyst with both permissions
        result = await protected_endpoint(current_user=analyst_user)

        assert result["status"] == "success"


# ============================================================================
# FastAPI Dependency Tests
# ============================================================================


class TestFastAPIDependencies:
    """Test FastAPI dependency injection for authorization."""

    @pytest.mark.asyncio
    async def test_get_current_user_with_role(self, mock_rbac_manager, analyst_user):
        """Test getting current user with role from JWT token."""
        from src.api.auth.dependencies import get_current_user_with_role

        # Mock JWT token payload
        token_payload = {
            "sub": str(analyst_user["id"]),
            "username": analyst_user["username"],
            "role": analyst_user["role"],
            "exp": 9999999999,
        }

        user_with_role = await get_current_user_with_role(token_payload, mock_rbac_manager)

        assert user_with_role["id"] == analyst_user["id"]
        assert user_with_role["role"] == analyst_user["role"]
        assert "permissions" in user_with_role

    @pytest.mark.asyncio
    async def test_authorize_endpoint_success(self, mock_rbac_manager, analyst_user):
        """Test endpoint authorization with valid permissions."""
        from src.api.auth.dependencies import authorize_endpoint

        # Should pass for analyst with data:write permission
        await authorize_endpoint(
            user=analyst_user,
            required_permission="data:write",
            rbac_manager=mock_rbac_manager,
        )

    @pytest.mark.asyncio
    async def test_authorize_endpoint_failure(self, mock_rbac_manager, viewer_user):
        """Test endpoint authorization with insufficient permissions."""
        from src.api.auth.dependencies import authorize_endpoint
        from fastapi import HTTPException

        # Should raise HTTPException for viewer without data:write permission
        with pytest.raises(HTTPException) as exc_info:
            await authorize_endpoint(
                user=viewer_user,
                required_permission="data:write",
                rbac_manager=mock_rbac_manager,
            )

        assert exc_info.value.status_code == 403


# ============================================================================
# Permission Definitions Tests
# ============================================================================


class TestPermissionDefinitions:
    """Test permission definitions and constants."""

    def test_permission_constants_exist(self):
        """Test that all required permission constants are defined."""
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

        assert DATA_READ == "data:read"
        assert DATA_WRITE == "data:write"
        assert DATA_DELETE == "data:delete"
        assert DATA_EXPORT == "data:export"
        assert JOBS_CREATE == "jobs:create"
        assert JOBS_READ == "jobs:read"
        assert JOBS_CANCEL == "jobs:cancel"
        assert USERS_MANAGE == "users:manage"
        assert SYSTEM_CONFIG == "system:config"

    def test_permission_groups(self):
        """Test permission groupings."""
        from src.api.auth.permissions import (
            DATA_PERMISSIONS,
            JOBS_PERMISSIONS,
            ADMIN_PERMISSIONS,
        )

        # Data permissions should include all data:* permissions
        assert "data:read" in DATA_PERMISSIONS
        assert "data:write" in DATA_PERMISSIONS
        assert "data:delete" in DATA_PERMISSIONS
        assert "data:export" in DATA_PERMISSIONS

        # Jobs permissions should include all jobs:* permissions
        assert "jobs:create" in JOBS_PERMISSIONS
        assert "jobs:read" in JOBS_PERMISSIONS
        assert "jobs:cancel" in JOBS_PERMISSIONS

        # Admin permissions should include users and system permissions
        assert "users:manage" in ADMIN_PERMISSIONS
        assert "system:config" in ADMIN_PERMISSIONS


# ============================================================================
# Endpoint Authorization Integration Tests
# ============================================================================


class TestEndpointAuthorization:
    """Test endpoint-level authorization enforcement."""

    @pytest.mark.asyncio
    async def test_data_read_endpoint_viewer_allowed(self, viewer_user):
        """Test that viewer can access data read endpoint."""
        from src.api.routes.data import read_dataset

        # Viewer should be able to read data
        result = await read_dataset(dataset_id="test", current_user=viewer_user)

        assert result is not None

    @pytest.mark.asyncio
    async def test_data_write_endpoint_viewer_denied(self, viewer_user):
        """Test that viewer cannot access data write endpoint."""
        from src.api.routes.data import write_dataset
        from fastapi import HTTPException

        # Viewer should be denied from writing data
        with pytest.raises(HTTPException) as exc_info:
            await write_dataset(dataset={"id": "test"}, current_user=viewer_user)

        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_data_write_endpoint_analyst_allowed(self, analyst_user):
        """Test that analyst can access data write endpoint."""
        from src.api.routes.data import write_dataset

        # Analyst should be able to write data
        result = await write_dataset(dataset={"id": "test"}, current_user=analyst_user)

        assert result is not None

    @pytest.mark.asyncio
    async def test_user_management_endpoint_admin_only(self, analyst_user, admin_user):
        """Test that user management endpoint is admin-only."""
        from src.api.routes.users import list_users
        from fastapi import HTTPException

        # Create mock objects with is_admin attribute (list_users checks current_user.is_admin)
        from unittest.mock import AsyncMock

        mock_user_service = AsyncMock()
        mock_user_service.list_users.return_value = ([], 0)

        analyst_obj = Mock()
        analyst_obj.id = analyst_user["id"]
        analyst_obj.is_admin = False

        admin_obj = Mock()
        admin_obj.id = admin_user["id"]
        admin_obj.is_admin = True

        # Analyst should be denied
        with pytest.raises(HTTPException) as exc_info:
            await list_users(current_user=analyst_obj, user_service=mock_user_service)

        assert exc_info.value.status_code == 403

        # Admin should be allowed
        result = await list_users(current_user=admin_obj, user_service=mock_user_service)

        assert result is not None

    @pytest.mark.asyncio
    async def test_system_config_endpoint_admin_only(self, analyst_user, admin_user):
        """Test that system config endpoint is admin-only."""
        from src.api.routes.system import get_config
        from fastapi import HTTPException

        # Analyst should be denied
        with pytest.raises(HTTPException) as exc_info:
            await get_config(current_user=analyst_user)

        assert exc_info.value.status_code == 403

        # Admin should be allowed
        result = await get_config(current_user=admin_user)

        assert result is not None


# ============================================================================
# Audit Logging Tests
# ============================================================================


class TestAuthorizationAuditLogging:
    """Test authorization audit logging."""

    @pytest.mark.asyncio
    async def test_authorization_success_logged(self, mock_rbac_manager, analyst_user):
        """Test that successful authorization is logged."""
        from src.api.auth.decorators import require_permission

        with patch("src.api.auth.decorators.log_authorization") as mock_log:
            from src.api.auth.decorators import require_permission

            @require_permission("data:write")
            async def protected_endpoint(current_user: dict = None):
                return {"status": "success"}

            result = await protected_endpoint(current_user=analyst_user)

            # Verify authorization success was logged
            mock_log.assert_called()
            call_args = mock_log.call_args
            assert call_args[1]["user_id"] == analyst_user["id"]
            assert call_args[1]["permission"] == "data:write"
            assert call_args[1]["granted"] is True

    @pytest.mark.asyncio
    async def test_authorization_failure_logged(self, mock_rbac_manager, viewer_user):
        """Test that authorization failures are logged."""
        from src.api.auth.decorators import require_permission

        with patch("src.api.auth.decorators.log_authorization") as mock_log:
            from src.api.auth.decorators import require_permission
            from fastapi import HTTPException

            @require_permission("data:write")
            async def protected_endpoint(current_user: dict = None):
                return {"status": "success"}

            with pytest.raises(HTTPException):
                await protected_endpoint(current_user=viewer_user)

            # Verify authorization failure was logged
            mock_log.assert_called()
            call_args = mock_log.call_args
            assert call_args[1]["user_id"] == viewer_user["id"]
            assert call_args[1]["permission"] == "data:write"
            assert call_args[1]["granted"] is False


# ============================================================================
# Edge Cases and Error Handling Tests
# ============================================================================


class TestRBACEdgeCases:
    """Test edge cases and error handling in RBAC."""

    def test_unknown_role_defaults_to_viewer(self, mock_rbac_manager):
        """Test that unknown role defaults to viewer permissions."""
        permissions = mock_rbac_manager.get_permissions("unknown_role")

        # Should get viewer permissions (default)
        assert "data:read" in permissions
        assert "jobs:read" in permissions

    def test_empty_role_defaults_to_viewer(self, mock_rbac_manager):
        """Test that empty role defaults to viewer permissions."""
        permissions = mock_rbac_manager.get_permissions("")

        # Should get viewer permissions (default)
        assert "data:read" in permissions

    def test_none_role_defaults_to_viewer(self, mock_rbac_manager):
        """Test that None role defaults to viewer permissions."""
        permissions = mock_rbac_manager.get_permissions(None)

        # Should get viewer permissions (default)
        assert "data:read" in permissions

    def test_circular_role_inheritance_handled(self):
        """Test that circular role inheritance is handled gracefully."""
        # Create config with circular inheritance
        circular_config = {
            "enabled": True,
            "default_role": "viewer",
            "roles": {
                "role_a": {"permissions": ["perm_a"], "inherits_from": ["role_b"]},
                "role_b": {"permissions": ["perm_b"], "inherits_from": ["role_a"]},
            },
        }

        from src.api.auth.rbac import RBACManager

        # Should not raise exception
        manager = RBACManager(config=circular_config)

        # Should resolve without infinite loop
        permissions = manager.get_permissions("role_a")

        assert "perm_a" in permissions
        assert "perm_b" in permissions

    def test_missing_permission_in_config(self, mock_rbac_manager):
        """Test checking for permission that doesn't exist in config."""
        # Should return False for non-existent permission
        result = mock_rbac_manager.has_permission("viewer", "nonexistent:permission")

        assert result is False

    def test_role_with_empty_permissions(self):
        """Test role with no permissions defined."""
        empty_config = {
            "enabled": True,
            "default_role": "empty",
            "roles": {
                "empty": {"permissions": [], "inherits_from": []},
            },
        }

        from src.api.auth.rbac import RBACManager

        manager = RBACManager(config=empty_config)
        permissions = manager.get_permissions("empty")

        # Should have empty permissions
        assert len(permissions) == 0


# ============================================================================
# Performance Tests
# ============================================================================


class TestRBACPerformance:
    """Test RBAC performance characteristics."""

    def test_permission_check_performance(self, mock_rbac_manager):
        """Test that permission checks are performant."""
        import time

        # Perform 1000 permission checks
        start = time.time()
        for _ in range(1000):
            mock_rbac_manager.has_permission("analyst", "data:read")
        elapsed = time.time() - start

        # Should complete in under 100ms (0.1ms per check)
        assert elapsed < 0.1

    def test_role_resolution_performance(self, mock_rbac_manager):
        """Test that role resolution with inheritance is performant."""
        import time

        # Perform 100 role resolutions with inheritance
        start = time.time()
        for _ in range(100):
            mock_rbac_manager.get_permissions("analyst")
        elapsed = time.time() - start

        # Should complete in under 50ms (0.5ms per resolution)
        assert elapsed < 0.05
