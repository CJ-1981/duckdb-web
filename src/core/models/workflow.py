"""
SPEC-WORKFLOW-001 Workflow Automation System Models

Database models for the workflow automation system including:
- WorkflowSpec: SPEC document storage and management
- WorkflowTask: Task execution tracking
- WorkflowExecution: Execution instance tracking
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.core.db.connection import Base


class TaskStatus(str, Enum):
    """Task execution status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExecutionStatus(str, Enum):
    """Workflow execution status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowSpec(Base):
    """SPEC document storage for workflow automation"""

    __tablename__ = "workflow_specs"

    id = Column(Integer, primary_key=True, index=True)
    spec_id = Column(String(50), unique=True, nullable=False, index=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    requirements = Column(JSON, nullable=False)  # EARS format requirements
    status = Column(String(50), default="planned", index=True)
    priority = Column(String(20), default="medium", index=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(String(100), nullable=True)

    # SPEC content
    specification = Column(Text, nullable=False)  # Full SPEC content
    acceptance_criteria = Column(JSON, nullable=True)  # Testable acceptance criteria

    # Relationships
    executions = relationship("WorkflowExecution", back_populates="spec")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "id": self.id,
            "spec_id": self.spec_id,
            "title": self.title,
            "description": self.description,
            "requirements": self.requirements,
            "status": self.status,
            "priority": self.priority,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by,
            "specification": self.specification,
            "acceptance_criteria": self.acceptance_criteria,
        }


class WorkflowTask(Base):
    """Individual task execution tracking"""

    __tablename__ = "workflow_tasks"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(50), unique=True, nullable=False, index=True)
    execution_id = Column(Integer, ForeignKey("workflow_executions.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Task metadata
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.PENDING, nullable=False)
    agent_assigned = Column(String(100), nullable=True)  # Which agent performed this task
    agent_type = Column(String(50), nullable=True)  # Subagent type

    # Task results and artifacts
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    execution_time = Column(Integer, nullable=True)  # Seconds

    # Task timing
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    started_at = Column(DateTime, nullable=True, index=True)
    completed_at = Column(DateTime, nullable=True, index=True)

    # Relationships
    execution = relationship("WorkflowExecution", back_populates="tasks")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "id": self.id,
            "task_id": self.task_id,
            "execution_id": self.execution_id,
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "agent_assigned": self.agent_assigned,
            "agent_type": self.agent_type,
            "input_data": self.input_data,
            "output_data": self.output_data,
            "error_message": self.error_message,
            "execution_time": self.execution_time,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class WorkflowExecution(Base):
    """Workflow execution instance tracking"""

    __tablename__ = "workflow_executions"

    id = Column(Integer, primary_key=True, index=True)
    execution_id = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False, index=True)
    spec_id = Column(Integer, ForeignKey("workflow_specs.id"), nullable=False, index=True)
    phase = Column(String(20), nullable=False, index=True)  # plan, run, sync

    # Execution metadata
    status = Column(SQLEnum(ExecutionStatus), default=ExecutionStatus.PENDING, nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    completed_at = Column(DateTime, nullable=True, index=True)
    duration = Column(Integer, nullable=True)  # Total execution time in seconds

    # Configuration and results
    config = Column(JSON, nullable=True)  # Runtime configuration
    results = Column(JSON, nullable=True)  # Final execution results
    artifacts = Column(JSON, nullable=True)  # Generated artifacts (docs, tests, etc.)
    errors = Column(JSON, nullable=True)  # Error collection

    # Agent tracking
    agents_used = Column(JSON, nullable=True)  # List of agents used
    tasks_count = Column(Integer, default=0, nullable=False)
    completed_tasks = Column(Integer, default=0, nullable=False)

    # Relationships
    spec = relationship("WorkflowSpec", back_populates="executions")
    tasks = relationship("WorkflowTask", back_populates="execution")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "id": self.id,
            "execution_id": str(self.execution_id),
            "spec_id": self.spec_id,
            "phase": self.phase,
            "status": self.status.value,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration": self.duration,
            "config": self.config,
            "results": self.results,
            "artifacts": self.artifacts,
            "errors": self.errors,
            "agents_used": self.agents_used,
            "tasks_count": self.tasks_count,
            "completed_tasks": self.completed_tasks,
        }