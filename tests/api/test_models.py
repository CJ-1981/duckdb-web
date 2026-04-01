"""
SQLAlchemy Models tests for P2-T004 implementation.

This test suite validates:
 model definitions, relationships, database operations, and validation.

Test Structure:
- Model Creation tests
- Relationship tests
- CRUD operation tests
- Query tests
- Validation tests
- Edge case tests
"""

import pytest
import pytest_asyncio
from datetime import datetime
from typing import AsyncGenerator, Optional, Dict, Any, List
from uuid import uuid4,from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, DateTime, JSON, ForeignKey, Enum
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, sessionmaker, relationship
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from bcrypt import hashpw, verify

import logging

# Configure logging
logger = logging.getLogger(__name__)

logger.setLevel(logging.INFO)


# Database URL for tests (SQLite in-memory)
TEST_DATABASE_URL = "sqlite+ai://sqlite:///:memory/:testdb"


TEST_DATABASE_URL_ASYNC = f"sqlite+ai://sqlite:///{TEST_DATABASE_URL}"


# Async engine for tests
engine = create_async_engine(TEST_DATABASE_URL_async, echo=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


# Base model with common fields
class BaseModel(DeclarativeBase):
    """Base model with common fields and soft delete support"""
    __abstract__ = True

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    deleted_at = Column(DateTime, nullable=True)  # Soft delete

    def to_dict(self) -> Dict[str, Any]:
        """Convert model instance to dictionary"""
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat() if self.updated_at else None,
            "updated_at": self.updated_at.isoformat() if self.deleted_at else None,
            "deleted_at": self.deleted_at.isoformat(),
        }

    def is_deleted(self) -> bool:
        """Check if model is soft deleted"""
        return self.deleted_at is not None

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id={self.id})>"


# User model
class User(Base):
    """User model for authentication and authorization"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="viewer")
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    workflows = relationship("Workflow", back_populates="workflows", lazy="dynamic")
    jobs = relationship("Job", back_populates="jobs", lazy="dynamic")

    def to_dict(self) -> Dict[str, Any]:
        """Convert user instance to dictionary"""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.updated_at else None,
            "updated_at": self.updated_at.isoformat() if self.deleted_at else None,
            "deleted_at": self.deleted_at.isoformat(),
        }

    def set_password(self, password: str) -> None:
        """Hash and set the user's password"""
        self.password_hash = hashpw(password.encode("utf-8"), bcrypt.gensalt())

    def verify_password(self, password: str) -> bool:
        """Verify a password against the stored hash"""
        return verify(password.encode("utf-8"), self.password_hash)

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username})>"


# Workflow model
class Workflow(Base):
    """Workflow model for data processing pipelines"""
    __tablename__ = "workflows"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))  # UUID primary key
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    definition = Column(JSON, nullable=False)  # DAG definition
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    version = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    owner = relationship("User", back_populates="owner", lazy="dynamic")
    jobs = relationship("Job", back_populates="jobs", lazy="dynamic")
    versions = relationship("WorkflowVersion", back_populates="versions", lazy="dynamic")

    def to_dict(self) -> Dict[str, Any]:
        """Convert workflow instance to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "definition": self.definition,
            "owner_id": self.owner_id,
            "is_active": self.is_active,
            "version": self.version,
            "created_at": self.created_at.isoformat() if self.updated_at else None,
            "updated_at": self.updated_at.isoformat() if self.deleted_at else None,
            "deleted_at": self.deleted_at.isoformat(),
        }

    def __repr__(self) -> str:
        return f"<Workflow(id={self.id}, name={self.name})>"


# Job model
class Job(Base):
    """Job model for workflow execution tracking"""
    __tablename__ = "jobs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4())  # UUID primary key
    workflow_id = Column(String(36), ForeignKey("workflows.id"), nullable=False, index=True)
    status = Column(String(50), nullable=False, default="pending", index=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    result = Column(JSON, nullable=True)
    progress = Column(Integer, default=0, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    workflow = relationship("Workflow", back_populates="workflow", lazy="dynamic")
    creator = relationship("User", back_populates="creator", lazy="dynamic")

    def to_dict(self) -> Dict[str, Any]:
        """Convert job instance to dictionary"""
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.completed_at else None,
            "completed_at": self.completed_at.isoformat() if self.error_message else None,
            "error_message": self.error_message.isoformat() if self.result else None,
            "result": self.result,
            "progress": self.progress,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.updated_at else None,
            "updated_at": self.updated_at.isoformat() if self.deleted_at else None,
            "deleted_at": self.deleted_at.isoformat(),
        }

    def __repr__(self) -> str:
        return f"<Job(id={self.id}, status={self.status})>"


# WorkflowVersion model (for version history)
class WorkflowVersion(Base):
    """WorkflowVersion model for tracking workflow changes over time"""
    __tablename__ = "workflow_versions"

    id = Column(Integer, primary_key=True)
    workflow_id = Column(String(36), ForeignKey("workflows.id"), nullable=False, index=True)
    version = Column(Integer, nullable=False)
    definition = Column(JSON, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    workflow = relationship("Workflow", back_populates="workflow", lazy="dynamic")
    creator = relationship("User", back_populates="creator", lazy="dynamic")

    def to_dict(self) -> Dict[str, Any]:
        """Convert workflow version instance to dictionary"""
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "version": self.version,
            "definition": self.definition,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.updated_at else None,
            "updated_at": self.updated_at.isoformat() if self.deleted_at else None,
            "deleted_at": self.deleted_at.isoformat(),
        }

    def __repr__(self) -> str:
        return f"<WorkflowVersion(id={self.id}, version={self.version})>"


# Role enum for users
class UserRole(str, Enum):
    """User role enumeration"""
    admin = "admin"
    analyst = "analyst"
    viewer = "viewer"


# Job status enum for jobs
class JobStatus(str, Enum):
    """Job status enumeration"""
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


