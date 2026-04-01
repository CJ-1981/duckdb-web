"""
Workflow Service

Business logic for workflow CRUD operations.
"""

from typing import List, Optional, Tuple
from datetime import datetime
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from src.api.models.workflow import Workflow
from src.api.models.workflow_version import WorkflowVersion
from src.api.schemas.workflow import WorkflowCreate, WorkflowUpdate


class WorkflowService:
    """Service for workflow business logic."""

    def __init__(self, db: AsyncSession):
        """
        Initialize workflow service.

        Args:
            db: Async database session
        """
        self.db = db

    async def create_workflow(
        self,
        workflow_data: WorkflowCreate,
        owner_id: int
    ) -> Workflow:
        """
        Create a new workflow.

        Args:
            workflow_data: Workflow creation data
            owner_id: ID of the user creating the workflow

        Returns:
            Created workflow object
        """
        workflow = Workflow(
            id=str(uuid4()),
            name=workflow_data.name,
            description=workflow_data.description,
            definition=workflow_data.definition.dict(),
            owner_id=owner_id,
            version=1
        )

        self.db.add(workflow)
        await self.db.commit()
        await self.db.refresh(workflow)

        # Create initial version entry
        await self._create_version_entry(workflow, owner_id)

        return workflow

    async def get_workflow(
        self,
        workflow_id: str,
        owner_id: int
    ) -> Optional[Workflow]:
        """
        Get workflow by ID (with ownership check).

        Args:
            workflow_id: Workflow UUID
            owner_id: ID of the user requesting the workflow

        Returns:
            Workflow object or None if not found
        """
        result = await self.db.execute(
            select(Workflow).where(
                and_(
                    Workflow.id == workflow_id,
                    Workflow.owner_id == owner_id,
                    Workflow.deleted_at.is_(None)
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_workflows(
        self,
        owner_id: int,
        is_active: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Workflow], int]:
        """
        List workflows with pagination.

        Args:
            owner_id: ID of the user requesting workflows
            is_active: Optional filter for active status
            page: Page number (1-indexed)
            page_size: Number of items per page

        Returns:
            Tuple of (workflows list, total count)
        """
        query = select(Workflow).where(
            and_(
                Workflow.owner_id == owner_id,
                Workflow.deleted_at.is_(None)
            )
        )

        if is_active is not None:
            query = query.where(Workflow.is_active == is_active)

        # Get total count
        count_result = await self.db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar() or 0

        # Apply pagination
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        workflows = result.scalars().all()

        return list(workflows), total

    async def update_workflow(
        self,
        workflow_id: str,
        workflow_data: WorkflowUpdate,
        owner_id: int
    ) -> Optional[Workflow]:
        """
        Update workflow.

        Args:
            workflow_id: Workflow UUID
            workflow_data: Update data
            owner_id: ID of the user updating the workflow

        Returns:
            Updated workflow or None if not found
        """
        workflow = await self.get_workflow(workflow_id, owner_id)
        if not workflow:
            return None

        # Update fields
        if workflow_data.name:
            workflow.name = workflow_data.name
        if workflow_data.description is not None:
            workflow.description = workflow_data.description
        if workflow_data.definition:
            workflow.definition = workflow_data.definition.dict()
            workflow.version += 1

        workflow.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(workflow)

        # Create version entry if definition changed
        if workflow_data.definition:
            await self._create_version_entry(workflow, owner_id)

        return workflow

    async def delete_workflow(
        self,
        workflow_id: str,
        owner_id: int
    ) -> bool:
        """
        Soft delete workflow.

        Args:
            workflow_id: Workflow UUID
            owner_id: ID of the user deleting the workflow

        Returns:
            True if deleted, False if not found
        """
        workflow = await self.get_workflow(workflow_id, owner_id)
        if not workflow:
            return False

        workflow.deleted_at = datetime.utcnow()
        workflow.is_active = False

        await self.db.commit()
        return True

    async def _create_version_entry(self, workflow: Workflow, created_by: int):
        """
        Create workflow version history entry.

        Args:
            workflow: Workflow to version
            created_by: ID of user who created the version
        """
        version = WorkflowVersion(
            workflow_id=workflow.id,
            version=workflow.version,
            definition=workflow.definition,
            created_by=created_by
        )
        self.db.add(version)
        await self.db.commit()
