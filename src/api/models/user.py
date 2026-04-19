"""
User model for authentication and authorization.

This module defines the User model with:
- Basic user information (username, email)
- Role-based access control (admin, analyst, viewer)
- Password hashing with bcrypt
- Relationships to workflows and jobs
"""

from typing import TYPE_CHECKING
from sqlalchemy import String, Boolean, Column, Enum as SQLEnum
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum

from .base import BaseModel

if TYPE_CHECKING:
    from .workflow import Workflow
    from .job import Job


# Role enumeration
class UserRole(str, PyEnum):
    """User role enumeration for RBAC"""
    admin = "admin"
    analyst = "analyst"
    viewer = "viewer"


class User(BaseModel):
    """User model for authentication and authorization"""

    __tablename__ = "users"

    # User information
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)  # bcrypt hash

    # Role and status
    role = Column(SQLEnum(UserRole), default=UserRole.viewer, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    # @MX:ANCHOR: User-workflow relationship (fan_in >= 3 callers expected)
    workflows = relationship("Workflow", back_populates="owner")
    # @MX:ANCHOR: User-job relationship (fan_in >= 3 callers expected)
    jobs = relationship("Job", back_populates="creator")
    # @MX:ANCHOR: User-workflow_version relationship (fan_in >= 3 callers expected)
    workflow_versions = relationship("WorkflowVersion", back_populates="creator")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username}, role={self.role})>"

    def set_password(self, password: str) -> None:
        """
        Hash and set the user's password.

        Args:
            password: Plain text password to hash

        Note: This method should be implemented with bcrypt
        """
        # This will be implemented when bcrypt is installed
        raise NotImplementedError("Password hashing requires bcrypt installation")

    def verify_password(self, password: str) -> bool:
        """
        Verify a password against the stored hash.

        Args:
            password: Plain text password to verify

        Returns:
            True if password matches, False otherwise

        Note: This method should be implemented with bcrypt
        """
        # This will be implemented when bcrypt is installed
        raise NotImplementedError("Password verification requires bcrypt installation")
