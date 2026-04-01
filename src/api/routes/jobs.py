"""
Job Routes

FastAPI routes for job operations.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.auth.dependencies import get_current_user, get_db
from src.api.auth.decorators import require_permission
from src.api.schemas.job import JobSubmit, JobResponse, JobListResponse
from src.api.services.job import JobService


router = APIRouter(prefix="/api/v1/jobs", tags=["Jobs"])


@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
@require_permission("workflows:execute")
async def submit_job(
    job_data: JobSubmit,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Submit a job for workflow execution.

    Requires permission: workflows:execute
    """
    service = JobService(db)

    # Get user ID from JWT token
    owner_id = int(current_user["sub"])

    job = await service.submit_job(job_data, owner_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )

    return job


@router.get("", response_model=JobListResponse)
@require_permission("jobs:read")
async def list_jobs(
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List jobs with pagination.

    Requires permission: jobs:read
    """
    service = JobService(db)

    # Get user ID from JWT token
    owner_id = int(current_user["sub"])

    jobs, total = await service.list_jobs(
        owner_id,
        status=status,
        page=page,
        page_size=page_size
    )

    return JobListResponse(
        jobs=jobs,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{job_id}", response_model=JobResponse)
@require_permission("jobs:read")
async def get_job(
    job_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get job status by ID.

    Requires permission: jobs:read
    """
    service = JobService(db)

    # Get user ID from JWT token
    owner_id = int(current_user["sub"])

    job = await service.get_job(job_id, owner_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

    return job


@router.post("/{job_id}/cancel", response_model=JobResponse)
@require_permission("jobs:write")
async def cancel_job(
    job_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Cancel a running job.

    Requires permission: jobs:write
    """
    service = JobService(db)

    # Get user ID from JWT token
    owner_id = int(current_user["sub"])

    success = await service.cancel_job(job_id, owner_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found or cannot be cancelled"
        )

    # Return updated job
    job = await service.get_job(job_id, owner_id)
    return job
