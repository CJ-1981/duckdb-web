"""
Job Schemas

Pydantic schemas for job operations.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID
from enum import Enum


class JobStatus(str, Enum):
    """Job status enumeration."""
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class JobSubmit(BaseModel):
    """Schema for submitting a job."""
    workflow_id: int = Field(..., description="Workflow ID to execute")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Execution parameters")


class JobResponse(BaseModel):
    """Schema for job response."""
    id: str  # UUID as string
    workflow_id: int
    status: JobStatus
    progress: float = Field(ge=0.0, le=100.0)
    error_message: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    created_by: int
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class JobListResponse(BaseModel):
    """Schema for paginated job list response."""
    jobs: list[JobResponse]
    total: int
    page: int
    page_size: int
