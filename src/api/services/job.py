"""
Job Service

Business logic for job operations.
"""

from typing import List, Optional, Tuple
from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, update
from sqlalchemy.sql import true

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

        @MX:ANCHOR: Job submission entry point (fan_in >= 3: API endpoint, test suite, scheduler)
        @MX:REASON: Centralized job creation ensures consistent validation and queue submission
        """
        # Verify workflow exists and user has access
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
            workflow_id=workflow.id,
            status=JobStatus.pending,
            progress=0.0,
            created_by=owner_id
        )

        self.db.add(job)
        await self.db.commit()
        await self.db.refresh(job)

        # Submit task to RQ for background execution
        try:
            from src.workflow.worker import get_redis_connection
            from rq import Queue
            import redis

            # Get Redis connection
            redis_conn = get_redis_connection()

            # Submit to spec_execution queue
            queue = Queue('spec_execution', connection=redis_conn)
            queue.enqueue(
                'src.workflow.worker.execute_workflow_job',
                job_id=job.id,
                workflow_definition=workflow.definition,
                job_timeout=3600,  # 1 hour timeout
                result_ttl=86400  # Keep results for 24 hours
            )

            # Update job status to indicate it's been queued
            job.status = JobStatus.pending
            await self.db.commit()

        except Exception as e:
            # Log error but don't fail job creation
            # Job will remain in pending state but won't execute
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to submit job {job.id} to RQ queue: {e}")

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

        # Update job status using SQL expression
        await self.db.execute(
            update(Job)
            .where(Job.id == job_id)
            .values(
                status=JobStatus.cancelled,
                completed_at=datetime.now(timezone.utc)
            )
        )
        await self.db.commit()

        # TODO: Cancel RQ task if running
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
