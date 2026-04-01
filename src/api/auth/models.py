"""
Role-Based Access Control (RBAC) models for authentication and authorization.

@MX:NOTE: RBAC models following SPEC-PLATFORM-001 requirements
@MX:SPEC: SPEC-PLATFORM-001 P2-T003
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class Role(BaseModel):
    """
    Role model representing a collection of permissions.

    @MX:ANCHOR: Core role model for RBAC system
    @MX:REASON: Used by RBACManager for role resolution
    """

    name: str = Field(..., description="Unique role name")
    permissions: List[str] = Field(default_factory=list, description="List of permission strings")
    inherits_from: List[str] = Field(default_factory=list, description="Parent roles to inherit from")
    description: Optional[str] = Field(None, description="Human-readable role description")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "analyst",
                "permissions": ["data:read", "data:write", "data:export"],
                "inherits_from": ["viewer"],
                "description": "Data analyst with read and write access",
            }
        }


class Permission(BaseModel):
    """
    Permission model representing a specific access right.

    @MX:NOTE: Granular permission definition following resource:action pattern
    """

    name: str = Field(..., description="Permission name in resource:action format")
    resource: str = Field(..., description="Resource being accessed (e.g., data, jobs, users)")
    action: str = Field(..., description="Action being performed (e.g., read, write, delete)")
    description: Optional[str] = Field(None, description="Human-readable permission description")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "data:read",
                "resource": "data",
                "action": "read",
                "description": "Read access to datasets",
            }
        }


class UserRole(BaseModel):
    """
    User-Role assignment model for tracking role assignments.

    @MX:NOTE: Tracks when and by whom a role was assigned to a user
    """

    user_id: int = Field(..., description="User ID")
    role_name: str = Field(..., description="Role name assigned to user")
    assigned_at: datetime = Field(..., description="Timestamp when role was assigned")
    assigned_by: Optional[int] = Field(None, description="User ID of admin who assigned the role")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 1,
                "role_name": "analyst",
                "assigned_at": "2024-01-01T12:00:00",
                "assigned_by": 2,
            }
        }


class RoleConfig(BaseModel):
    """
    Configuration model for role definition from config files.

    @MX:NOTE: Used to parse role configuration from YAML
    """

    permissions: List[str] = Field(default_factory=list, description="List of permission strings")
    inherits_from: List[str] = Field(default_factory=list, description="Parent roles to inherit from")
    description: Optional[str] = Field(None, description="Human-readable role description")


class RBACConfig(BaseModel):
    """
    Complete RBAC configuration model.

    @MX:ANCHOR: Top-level RBAC configuration structure
    @MX:REASON: Single source of truth for RBAC settings
    """

    enabled: bool = Field(default=True, description="Enable/disable RBAC")
    default_role: str = Field(default="viewer", description="Default role for new users")
    roles: dict[str, RoleConfig] = Field(
        default_factory=dict, description="Role definitions mapping role name to configuration"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "enabled": True,
                "default_role": "viewer",
                "roles": {
                    "admin": {"permissions": ["*"], "inherits_from": []},
                    "analyst": {
                        "permissions": ["data:read", "data:write"],
                        "inherits_from": ["viewer"],
                    },
                    "viewer": {"permissions": ["data:read"], "inherits_from": []},
                },
            }
        }
