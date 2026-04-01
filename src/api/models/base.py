"""
Base model with common fields for all SQLAlchemy models.

This module provides:
- Abstract base model with id, timestamps, and soft delete support
- Common utility methods for all models
- Database session management for async operations
"""

from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.orm import DeclarativeBase, declared_attr


class BaseModel(DeclarativeBase):
    """Abstract base model with common fields and soft delete support"""

    __abstract__ = True

    # Primary key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Soft delete
    deleted_at = Column(DateTime, nullable=True)

    def to_dict(self) -> Dict[str, Any]:
        """Convert model instance to dictionary"""
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }

    def is_deleted(self) -> bool:
        """Check if model is soft deleted"""
        return self.deleted_at is not None

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id={self.id})>"


# Database session management
async def get_async_session() -> Any:
    """Get async database session"""
    # This will be implemented in __init__.py
    # For now, raise NotImplementedError
    raise NotImplementedError("Database session not configured. Configure in src.api.models.__init__.py")


