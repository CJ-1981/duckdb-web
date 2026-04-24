"""
Job model for workflow execution tracking.

This module defines the Job model with
- Execution status tracking
- Progress monitoring
- Error handling
- Result storage
- Relationships to workflow and creator
"""

from typing import TYPE_CHECKING
from sqlalchemy import String, Float, DateTime, JSON, Enum as SQLEnum, Integer, Column, ForeignKey
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum

from .base import BaseModel

if TYPE_CHECKING:
    from .user import User
    from .workflow import Workflow


# Job status enumeration
class JobStatus(str, PyEnum):
    """Job status enumeration for execution tracking"""
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class Job(BaseModel):
    """Job model for workflow execution tracking"""

    __tablename__ = "jobs"

    # Job identification
    id = Column(String(36), primary_key=True)  # UUID as string

    workflow_id = Column(Integer, ForeignKey("workflows.id"), nullable=False, index=True)

    # Execution status
    status = Column(SQLEnum(JobStatus), default=JobStatus.pending, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Progress and results
    progress = Column(Float, default=0.0, nullable=False)
    error_message = Column(String, nullable=True)
    result = Column(JSON, nullable=True)

    # Creator
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Relationships
    # @MX:ANCHOR: Job-workflow relationship (fan_in >= 3 callers expected)
    workflow = relationship("Workflow", back_populates="jobs")
    # @MX:ANCHOR: Job-creator relationship (fan_in >= 3 callers expected)
    creator = relationship("User", back_populates="jobs")

    def __init__(self, **kwargs):
        """Initialize Job with Python-level defaults."""
        super().__init__(**kwargs)
        # Apply Python-level defaults
        if self.status is None:
            self.status = JobStatus.pending
        if self.progress is None:
            self.progress = 0.0

    def __repr__(self) -> str:
        return f"<Job(id={self.id}, status={self.status}, progress={self.progress})>"

    def to_dict(self) -> dict:
        """Convert job to dictionary including all fields."""
        result = super().to_dict()
        # Add Job-specific fields
        result.update({
            "workflow_id": self.workflow_id,
            "status": self.status.value if self.status else None,
            "progress": self.progress,
            "error_message": self.error_message,
            "created_by": self.created_by,
        })
        # Add optional fields
        if self.started_at:
            result["started_at"] = self.started_at.isoformat() if self.started_at else None
        if self.completed_at:
            result["completed_at"] = self.completed_at.isoformat() if self.completed_at else None
        if self.result:
            result["result"] = self.result
        return result
