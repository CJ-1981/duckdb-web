"""
Workflow Schemas

Pydantic schemas for workflow CRUD operations.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional
from datetime import datetime
from uuid import UUID


class WorkflowNodeConfig(BaseModel):
    """Configuration for a workflow node."""
    node_type: str = Field(..., description="Type of node")
    config: Dict[str, Any] = Field(default_factory=dict)


class WorkflowNode(BaseModel):
    """A node in the workflow DAG."""
    id: str = Field(..., min_length=1, max_length=100)
    type: str = Field(..., description="Node type")
    config: Dict[str, Any] = Field(default_factory=dict)


class WorkflowEdge(BaseModel):
    """An edge connecting two workflow nodes."""
    source: str
    target: str


class WorkflowDefinition(BaseModel):
    """Definition of a workflow DAG (nodes and edges)."""
    nodes: List[WorkflowNode]
    edges: List[WorkflowEdge]

    @validator('nodes')
    def validate_unique_node_ids(cls, v):
        """Ensure all node IDs are unique."""
        ids = [node.id for node in v]
        if len(ids) != len(set(ids)):
            raise ValueError("Node IDs must be unique")
        return v

    @validator('edges')
    def validate_edge_references(cls, v, values):
        """Ensure all edges reference valid nodes."""
        if 'nodes' not in values:
            return v

        node_ids = {node.id for node in values['nodes']}
        for edge in v:
            if edge.source not in node_ids:
                raise ValueError(f"Edge references non-existent node: {edge.source}")
            if edge.target not in node_ids:
                raise ValueError(f"Edge references non-existent node: {edge.target}")
        return v


class WorkflowBase(BaseModel):
    """Base workflow fields."""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)


class WorkflowCreate(WorkflowBase):
    """Schema for creating a workflow."""
    definition: WorkflowDefinition


class WorkflowUpdate(WorkflowBase):
    """Schema for updating a workflow."""
    definition: Optional[WorkflowDefinition] = None


class WorkflowResponse(WorkflowBase):
    """Schema for workflow response."""
    id: UUID
    owner_id: int
    is_active: bool
    version: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WorkflowListResponse(BaseModel):
    """Schema for paginated workflow list response."""
    workflows: List[WorkflowResponse]
    total: int
    page: int
    page_size: int
