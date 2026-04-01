"""
Comprehensive test suite for Job Execution endpoints following TDD methodology.

Tests are designed to document expected behavior for:
- Job submission and creation
- Job status tracking
- Job result retrieval
- Job cancellation

@MX:SPEC: SPEC-PLATFORM-001 P2-T006
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from typing import Dict, Any
from uuid import uuid4

from httpx import AsyncClient, ASGITransport
from fastapi import status


# ============================================================================
# Helper Functions for Testing
# ============================================================================

def setup_auth_mocks(app, mock_db_session, mock_current_user):
    """
    Setup FastAPI dependency overrides for authentication and database.

    This helper function configures the app to use mock dependencies during testing,
    allowing tests to bypass real database operations and authentication.

    Args:
        app: FastAPI application instance
        mock_db_session: Mock database session
        mock_current_user: Mock current user dict

    Returns:
        None (modifies app.dependency_overrides in place)
    """
    from src.api.routes import jobs
    from unittest.mock import AsyncMock

    # Create wrapper that returns the mock directly (not async)
    def override_get_db():
        return mock_db_session

    def override_get_user():
        return mock_current_user

    app.dependency_overrides[jobs.get_db] = override_get_db
    app.dependency_overrides[jobs.get_current_user] = override_get_user


def cleanup_auth_mocks(app):
    """
    Cleanup FastAPI dependency overrides after testing.

    Args:
        app: FastAPI application instance
    """
    app.dependency_overrides = {}


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def app():
    """Create FastAPI app for testing."""
    from src.api.main import create_app
    app = create_app()
    return app


@pytest.fixture
def mock_db_session():
    """Create mock database session."""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.add = Mock()
    return session


@pytest.fixture
def mock_current_user():
    """Create mock current user dict for authentication."""
    return {
        "sub": "1",
        "username": "testuser",
        "role": "analyst",
        "permissions": ["workflows:execute", "jobs:read", "jobs:write"]
    }


@pytest.fixture
def mock_workflow():
    """Create mock workflow for testing."""
    workflow = Mock()
    workflow.id = 123  # Integer ID like the real model
    workflow.name = "Test Workflow"
    workflow.description = "A test workflow"
    workflow.owner_id = 1
    workflow.is_active = True
    workflow.version = 1
    workflow.created_at = datetime.utcnow()
    workflow.updated_at = datetime.utcnow()
    workflow.definition = {
        "nodes": [
            {"id": "node1", "type": "data_source", "config": {"connector": "csv", "path": "data.csv"}},
            {"id": "node2", "type": "transform", "config": {"operation": "filter", "expression": "age > 18"}},
            {"id": "node3", "type": "data_sink", "config": {"format": "parquet", "path": "output.parquet"}}
        ],
        "edges": [
            {"source": "node1", "target": "node2"},
            {"source": "node2", "target": "node3"}
        ]
    }
    return workflow


@pytest.fixture
def valid_job_data(mock_workflow):
    """Create valid job submission data for testing."""
    return {
        "workflow_id": mock_workflow.id,  # Integer ID
        "parameters": {}
    }


# ============================================================================
# Job Submission Tests - Create
# ============================================================================

class TestJobSubmission:
    """Test job submission endpoint."""

    @pytest.mark.asyncio
    async def test_submit_job_success(
        self, app, mock_db_session, mock_current_user, mock_workflow, valid_job_data
    ):
        """Test successful job submission."""
        from src.api.routes import jobs
        from unittest.mock import Mock

        app.include_router(jobs.router)

        # Mock the service layer
        mock_job = Mock()
        mock_job.id = str(uuid4())
        mock_job.workflow_id = mock_workflow.id
        mock_job.status = "pending"
        mock_job.progress = 0.0
        mock_job.created_by = 1
        mock_job.created_at = datetime.utcnow()
        mock_job.started_at = None
        mock_job.completed_at = None
        mock_job.error_message = None
        mock_job.result = None
        mock_job.started_at = None
        mock_job.completed_at = None
        mock_job.error_message = None
        mock_job.result = None

        async def mock_submit(*args, **kwargs):
            return mock_job

        # Setup authentication mocks
        setup_auth_mocks(app, mock_db_session, mock_current_user)

        try:
            with patch.object(jobs.JobService, "submit_job", mock_submit):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    response = await client.post(
                        "/api/v1/jobs",
                        json=valid_job_data,
                        headers={"Authorization": "Bearer 1:testuser:analyst"}
                    )
        finally:
            cleanup_auth_mocks(app)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "id" in data
        assert data["workflow_id"] == mock_workflow.id
        assert data["status"] == "pending"
        assert data["progress"] == 0.0

    @pytest.mark.asyncio
    async def test_submit_job_with_parameters(
        self, app, mock_db_session, mock_current_user, mock_workflow
    ):
        """Test job submission with custom parameters."""
        from src.api.routes import jobs
        from unittest.mock import Mock

        app.include_router(jobs.router)

        job_data = {
            "workflow_id": mock_workflow.id,
            "parameters": {
                "limit": 1000,
                "output_format": "json"
            }
        }

        # Mock the service layer
        mock_job = Mock()
        mock_job.id = str(uuid4())
        mock_job.workflow_id = mock_workflow.id
        mock_job.status = "pending"
        mock_job.progress = 0.0
        mock_job.created_by = 1
        mock_job.created_at = datetime.utcnow()
        mock_job.started_at = None
        mock_job.completed_at = None
        mock_job.error_message = None
        mock_job.result = None

        async def mock_submit(*args, **kwargs):
            return mock_job

        # Setup authentication mocks
        setup_auth_mocks(app, mock_db_session, mock_current_user)

        try:
            with patch.object(jobs.JobService, "submit_job", mock_submit):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    response = await client.post(
                        "/api/v1/jobs",
                        json=job_data,
                        headers={"Authorization": "Bearer 1:testuser:analyst"}
                    )
        finally:
            cleanup_auth_mocks(app)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["workflow_id"] == mock_workflow.id

    @pytest.mark.asyncio
    async def test_submit_job_workflow_not_found(
        self, app, mock_db_session, mock_current_user
    ):
        """Test job submission with non-existent workflow."""
        from src.api.routes import jobs

        app.include_router(jobs.router)

        job_data = {
            "workflow_id": 99999,  # Non-existent workflow ID (integer)
            "parameters": {}
        }

        # Mock the service layer
        async def mock_submit(*args, **kwargs):
            return None

        # Setup authentication mocks
        setup_auth_mocks(app, mock_db_session, mock_current_user)

        try:
            with patch.object(jobs.JobService, "submit_job", mock_submit):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    response = await client.post(
                        "/api/v1/jobs",
                        json=job_data,
                        headers={"Authorization": "Bearer 1:testuser:analyst"}
                    )
        finally:
            cleanup_auth_mocks(app)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_submit_job_invalid_workflow_id(
        self, app, mock_db_session, mock_current_user
    ):
        """Test job submission with invalid workflow ID format."""
        from src.api.routes import jobs

        app.include_router(jobs.router)

        job_data = {
            "workflow_id": "not-an-integer",  # Invalid format (string instead of int)
            "parameters": {}
        }

        # Setup authentication mocks
        setup_auth_mocks(app, mock_db_session, mock_current_user)

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/jobs",
                    json=job_data,
                    headers={"Authorization": "Bearer 1:testuser:analyst"}
                )
        finally:
            cleanup_auth_mocks(app)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ============================================================================
# Job Status Tests - Get
# ============================================================================

class TestJobStatus:
    """Test job status retrieval endpoint."""

    @pytest.mark.asyncio
    async def test_get_job_status_success(
        self, app, mock_db_session, mock_current_user, mock_workflow
    ):
        """Test successful job status retrieval."""
        from src.api.routes import jobs
        from unittest.mock import Mock

        app.include_router(jobs.router)

        # Mock job object
        mock_job = Mock()
        mock_job.id = str(uuid4())
        mock_job.workflow_id = mock_workflow.id
        mock_job.status = "running"
        mock_job.progress = 45.0
        mock_job.created_by = 1
        mock_job.created_at = datetime.utcnow()
        mock_job.started_at = datetime.utcnow()
        mock_job.completed_at = None
        mock_job.error_message = None
        mock_job.result = None

        # Mock the service layer
        async def mock_get(*args, **kwargs):
            return mock_job

        # Setup authentication mocks
        setup_auth_mocks(app, mock_db_session, mock_current_user)

        try:
            with patch.object(jobs.JobService, "get_job", mock_get):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    response = await client.get(
                        f"/api/v1/jobs/{mock_job.id}",
                        headers={"Authorization": "Bearer 1:testuser:analyst"}
                    )
        finally:
            cleanup_auth_mocks(app)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == mock_job.id
        assert data["status"] == "running"
        assert data["progress"] == 45.0

    @pytest.mark.asyncio
    async def test_get_job_status_completed(
        self, app, mock_db_session, mock_current_user, mock_workflow
    ):
        """Test job status retrieval for completed job."""
        from src.api.routes import jobs
        from unittest.mock import Mock

        app.include_router(jobs.router)

        # Mock completed job object
        mock_job = Mock()
        mock_job.id = str(uuid4())
        mock_job.workflow_id = mock_workflow.id
        mock_job.status = "completed"
        mock_job.progress = 100.0
        mock_job.created_by = 1
        mock_job.created_at = datetime.utcnow()
        mock_job.started_at = datetime.utcnow()
        mock_job.completed_at = datetime.utcnow()
        mock_job.error_message = None
        mock_job.result = {"row_count": 1000, "output_path": "/tmp/output.parquet"}

        # Mock the service layer
        async def mock_get(*args, **kwargs):
            return mock_job

        # Setup authentication mocks
        setup_auth_mocks(app, mock_db_session, mock_current_user)

        try:
            with patch.object(jobs.JobService, "get_job", mock_get):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    response = await client.get(
                        f"/api/v1/jobs/{mock_job.id}",
                        headers={"Authorization": "Bearer 1:testuser:analyst"}
                    )
        finally:
            cleanup_auth_mocks(app)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "completed"
        assert data["progress"] == 100.0
        assert data["result"] is not None

    @pytest.mark.asyncio
    async def test_get_job_status_failed(
        self, app, mock_db_session, mock_current_user, mock_workflow
    ):
        """Test job status retrieval for failed job."""
        from src.api.routes import jobs
        from unittest.mock import Mock

        app.include_router(jobs.router)

        # Mock failed job object
        mock_job = Mock()
        mock_job.id = str(uuid4())
        mock_job.workflow_id = mock_workflow.id
        mock_job.status = "failed"
        mock_job.progress = 35.0
        mock_job.created_by = 1
        mock_job.created_at = datetime.utcnow()
        mock_job.started_at = datetime.utcnow()
        mock_job.completed_at = datetime.utcnow()
        mock_job.error_message = "Division by zero error"
        mock_job.result = None

        # Mock the service layer
        async def mock_get(*args, **kwargs):
            return mock_job

        # Setup authentication mocks
        setup_auth_mocks(app, mock_db_session, mock_current_user)

        try:
            with patch.object(jobs.JobService, "get_job", mock_get):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    response = await client.get(
                        f"/api/v1/jobs/{mock_job.id}",
                        headers={"Authorization": "Bearer 1:testuser:analyst"}
                    )
        finally:
            cleanup_auth_mocks(app)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "failed"
        assert data["error_message"] is not None

    @pytest.mark.asyncio
    async def test_get_job_status_not_found(
        self, app, mock_db_session, mock_current_user
    ):
        """Test job status retrieval with non-existent job ID."""
        from src.api.routes import jobs

        app.include_router(jobs.router)

        # Mock the service layer
        async def mock_get(*args, **kwargs):
            return None

        # Setup authentication mocks
        setup_auth_mocks(app, mock_db_session, mock_current_user)

        try:
            with patch.object(jobs.JobService, "get_job", mock_get):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    response = await client.get(
                        f"/api/v1/jobs/{str(uuid4())}",
                        headers={"Authorization": "Bearer 1:testuser:analyst"}
                    )
        finally:
            cleanup_auth_mocks(app)

        assert response.status_code == status.HTTP_404_NOT_FOUND


# ============================================================================
# Job List Tests
# ============================================================================

class TestJobList:
    """Test job list endpoint."""

    @pytest.mark.asyncio
    async def test_list_jobs_success(
        self, app, mock_db_session, mock_current_user, mock_workflow
    ):
        """Test successful job list retrieval."""
        from src.api.routes import jobs
        from unittest.mock import Mock

        app.include_router(jobs.router)

        # Mock job objects
        mock_jobs = []
        for i in range(3):
            job = Mock()
            job.id = str(uuid4())
            job.workflow_id = mock_workflow.id
            job.status = ["pending", "running", "completed"][i]
            job.progress = [0.0, 50.0, 100.0][i]
            job.created_by = 1
            job.created_at = datetime.utcnow()
            job.started_at = datetime.utcnow() if i > 0 else None
            job.completed_at = datetime.utcnow() if i == 2 else None
            job.error_message = None
            job.result = {"count": i * 100} if i == 2 else None
            mock_jobs.append(job)

        # Mock the service layer
        async def mock_list(*args, **kwargs):
            return mock_jobs, len(mock_jobs)

        # Setup authentication mocks
        setup_auth_mocks(app, mock_db_session, mock_current_user)

        try:
            with patch.object(jobs.JobService, "list_jobs", mock_list):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    response = await client.get(
                        "/api/v1/jobs",
                        headers={"Authorization": "Bearer 1:testuser:analyst"}
                    )
        finally:
            cleanup_auth_mocks(app)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "jobs" in data
        assert data["total"] == 3
        assert len(data["jobs"]) == 3

    @pytest.mark.asyncio
    async def test_list_jobs_empty(
        self, app, mock_db_session, mock_current_user
    ):
        """Test job list when no jobs exist."""
        from src.api.routes import jobs

        app.include_router(jobs.router)

        # Mock the service layer
        async def mock_list(*args, **kwargs):
            return [], 0

        # Setup authentication mocks
        setup_auth_mocks(app, mock_db_session, mock_current_user)

        try:
            with patch.object(jobs.JobService, "list_jobs", mock_list):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    response = await client.get(
                        "/api/v1/jobs",
                        headers={"Authorization": "Bearer 1:testuser:analyst"}
                    )
        finally:
            cleanup_auth_mocks(app)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["jobs"] == []
        assert data["total"] == 0


# ============================================================================
# Job Cancellation Tests
# ============================================================================

class TestJobCancellation:
    """Test job cancellation endpoint."""

    @pytest.mark.asyncio
    async def test_cancel_job_success(
        self, app, mock_db_session, mock_current_user, mock_workflow
    ):
        """Test successful job cancellation."""
        from src.api.routes import jobs
        from unittest.mock import Mock

        app.include_router(jobs.router)

        # Mock job object
        mock_job = Mock()
        mock_job.id = str(uuid4())
        mock_job.workflow_id = mock_workflow.id
        mock_job.status = "running"
        mock_job.progress = 45.0
        mock_job.created_by = 1
        mock_job.created_at = datetime.utcnow()
        mock_job.started_at = datetime.utcnow()
        mock_job.completed_at = None
        mock_job.error_message = None
        mock_job.result = None

        # Mock the service layer
        async def mock_cancel(*args, **kwargs):
            mock_job.status = "cancelled"
            mock_job.completed_at = datetime.utcnow()
            return True

        async def mock_get(*args, **kwargs):
            return mock_job

        # Setup authentication mocks
        setup_auth_mocks(app, mock_db_session, mock_current_user)

        try:
            with patch.multiple(jobs.JobService, cancel_job=mock_cancel, get_job=mock_get):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    response = await client.post(
                        f"/api/v1/jobs/{mock_job.id}/cancel",
                        headers={"Authorization": "Bearer 1:testuser:analyst"}
                    )
        finally:
            cleanup_auth_mocks(app)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "cancelled"

    @pytest.mark.asyncio
    async def test_cancel_job_already_completed(
        self, app, mock_db_session, mock_current_user, mock_workflow
    ):
        """Test cancelling a job that is already completed."""
        from src.api.routes import jobs

        app.include_router(jobs.router)

        # Mock the service layer
        async def mock_cancel(*args, **kwargs):
            return False  # Cannot cancel completed job

        async def mock_get(*args, **kwargs):
            return None  # Not found

        # Setup authentication mocks
        setup_auth_mocks(app, mock_db_session, mock_current_user)

        try:
            with patch.multiple(jobs.JobService, cancel_job=mock_cancel, get_job=mock_get):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    response = await client.post(
                        f"/api/v1/jobs/{str(uuid4())}/cancel",
                        headers={"Authorization": "Bearer 1:testuser:analyst"}
                    )
        finally:
            cleanup_auth_mocks(app)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_cancel_job_not_found(
        self, app, mock_db_session, mock_current_user
    ):
        """Test cancelling a non-existent job."""
        from src.api.routes import jobs

        app.include_router(jobs.router)

        # Mock the service layer
        async def mock_cancel(*args, **kwargs):
            return False

        async def mock_get(*args, **kwargs):
            return None

        # Setup authentication mocks
        setup_auth_mocks(app, mock_db_session, mock_current_user)

        try:
            with patch.multiple(jobs.JobService, cancel_job=mock_cancel, get_job=mock_get):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    response = await client.post(
                        f"/api/v1/jobs/{str(uuid4())}/cancel",
                        headers={"Authorization": "Bearer 1:testuser:analyst"}
                    )
        finally:
            cleanup_auth_mocks(app)

        assert response.status_code == status.HTTP_404_NOT_FOUND
