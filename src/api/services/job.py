"""
Job Service

Business logic for job operations.
"""

from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, update

from src.api.models.job import Job, JobStatus
from src.api.models.workflow import Workflow
from src.api.models.user import User
from src.api.schemas.job import JobSubmit


class JobService:
    """Service for job business logic."""

    def __init__(self, db: AsyncSession):
        """
        Initialize job service.

        Args:
            db: Async database session
        """
        self.db = db

    async def submit_job(
        self,
        job_data: JobSubmit,
        owner_id: int
    ) -> Optional[Job]:
        """
        Submit a new job for workflow execution.

        Args:
            job_data: Job submission data
            owner_id: ID of the user submitting the job

        Returns:
            Created job object or None if workflow not found
        """
        # Verify workflow exists and user has access
        # Note: job_data.workflow_id is a UUID from the API, but Workflow.id is an integer
        # We need to match by the integer ID stored in the workflow
        # For now, we'll use the UUID to look up the workflow by its string representation
        # In a real implementation, you'd have a separate UUID field on Workflow

        # For TDD GREEN phase: Just create the job with the provided workflow_id
        # The workflow_id in JobSubmit is expected to be the integer workflow ID

        workflow_result = await self.db.execute(
            select(Workflow).where(
                and_(
                    Workflow.id == job_data.workflow_id,
                    Workflow.owner_id == owner_id,
                    Workflow.deleted_at.is_(None)
                )
            )
        )
        workflow = workflow_result.scalar_one_or_none()

        if not workflow:
            return None

        # Create job record
        job = Job(
            id=str(uuid4()),
            workflow_id=workflow.id,  # Store the integer workflow ID
            status=JobStatus.pending,
            progress=0.0,
            created_by=owner_id
        )

        self.db.add(job)
        await self.db.commit()
        await self.db.refresh(job)

        # TODO: Submit task to Celery for background execution
        # For now, job remains in pending state

        return job

    async def get_job(
        self,
        job_id: str,
        owner_id: int
    ) -> Optional[Job]:
        """
        Get job by ID (with ownership check).

        Args:
            job_id: Job UUID
            owner_id: ID of the user requesting the job

        Returns:
            Job object or None if not found
        """
        result = await self.db.execute(
            select(Job).where(
                and_(
                    Job.id == job_id,
                    Job.created_by == owner_id
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_jobs(
        self,
        owner_id: int,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Job], int]:
        """
        List jobs with pagination.

        Args:
            owner_id: ID of the user requesting jobs
            status: Optional filter by job status
            page: Page number (1-indexed)
            page_size: Number of items per page

        Returns:
            Tuple of (jobs list, total count)
        """
        query = select(Job).where(Job.created_by == owner_id)

        if status:
            query = query.where(Job.status == status)

        # Get total count
        count_result = await self.db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar() or 0

        # Apply pagination and ordering
        query = query.order_by(Job.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        jobs = result.scalars().all()

        return list(jobs), total

    async def cancel_job(
        self,
        job_id: str,
        owner_id: int
    ) -> bool:
        """
        Cancel a running job.

        Args:
            job_id: Job UUID
            owner_id: ID of the user cancelling the job

        Returns:
            True if cancelled, False if not found or cannot be cancelled
        """
        job = await self.get_job(job_id, owner_id)
        if not job:
            return False

        # Can only cancel pending or running jobs
        if job.status not in [JobStatus.pending, JobStatus.running]:
            return False

        # Update job status
        job.status = JobStatus.cancelled
        job.completed_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(job)

        # TODO: Cancel Celery task if running
        # For now, just update the status

        return True

    async def update_job_status(
        self,
        job_id: str,
        status: JobStatus,
        **kwargs
    ) -> Optional[Job]:
        """
        Update job status and trigger notifications.

        Args:
            job_id: Job UUID
            status: New job status
            **kwargs: Additional job fields to update (progress, result, error_message, etc.)

        Returns:
            Updated job object or None if not found

        @MX:ANCHOR: Job status update entry point (fan_in >= 3: workflow task, export task, direct calls)
        """
        # Build update values
        values = {"status": status}
        values.update(kwargs)

        # Update job in database
        await self.db.execute(
            update(Job).where(Job.id == job_id).values(**values)
        )
        await self.db.commit()

        # Fetch updated job with user
        result = await self.db.execute(
            select(Job, User).join(
                User, Job.created_by == User.id
            ).where(Job.id == job_id)
        )
        row = result.first()

        if not row:
            return None

        job, user = row

        # Send notification based on status
        from src.api.services.notification import get_notification_service

        notification_service = get_notification_service()

        if status == JobStatus.completed:
            await notification_service.send_completion_notification(job, user)
        elif status == JobStatus.failed:
            await notification_service.send_failure_notification(job, user)

        return job
