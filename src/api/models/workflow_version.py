"""
WorkflowVersion model for workflow version history.

This module defines the WorkflowVersion model with
- Version tracking for workflow changes
- Definition snapshots
- Audit trail for changes
- Relationships to workflow and creator
"""

from typing import TYPE_CHECKING
from sqlalchemy import String, Integer, Text, JSON, Column
from sqlalchemy.orm import relationship

from .base import BaseModel

if TYPE_CHECKING:
    from .user import User
    from .workflow import Workflow


class WorkflowVersion(BaseModel):
    """WorkflowVersion model for workflow version history"""

    __tablename__ = "workflow_versions"

    # Version identification
    workflow_id = Column(Integer, nullable=False, index=True)
    version = Column(Integer, nullable=False)

    # Version definition
    definition = Column(JSON, nullable=False)

    # Audit trail
    created_by = Column(Integer, nullable=False, index=True)

    # Relationships
    # @MX:ANCHOR: WorkflowVersion-workflow relationship (fan_in >= 3 callers expected)
    workflow = relationship("Workflow", back_populates="versions")
    # @MX:ANCHOR: WorkflowVersion-creator relationship (fan_in >= 3 callers expected)
    creator = relationship("User", back_populates="workflow_versions")

    def __repr__(self) -> str:
        return f"<WorkflowVersion(id={self.id}, workflow_id={self.workflow_id}, version={self.version})>"

    def to_dict(self) -> dict:
        """Convert workflow version to dictionary with definition"""
        result = super().to_dict()
        result["definition"] = self.definition
        return result
