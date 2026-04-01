"""
Job Status Notification Tests

Tests for job status tracking and notification system.
Following TDD methodology: RED phase first.

@MX:SPEC: SPEC-PLATFORM-001 P2-T008
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from uuid import uuid4


class TestNotificationService:
    """Test notification service for job status updates."""

    @pytest.mark.asyncio
    async def test_send_completion_notification(self):
        """Test sending completion notification."""
        from src.api.services.notification import NotificationService
        from src.api.models.job import JobStatus

        # Create notification service
        notification_service = NotificationService()

        # Create mock job
        mock_job = Mock()
        mock_job.id = str(uuid4())
        mock_job.status = JobStatus.completed
        mock_job.progress = 100.0
        mock_job.result = {"row_count": 1000}
        mock_job.created_by = 1
        mock_job.workflow_id = 123

        # Mock user
        mock_user = Mock()
        mock_user.id = 1
        mock_user.email = "user@example.com"
        mock_user.username = "testuser"

        # Send notification
        await notification_service.send_completion_notification(mock_job, mock_user)

        # Verify notification was sent (check in-memory storage)
        notifications = notification_service.get_notifications(mock_user.id)
        assert len(notifications) == 1
        assert notifications[0]["type"] == "job_completed"
        assert notifications[0]["job_id"] == mock_job.id
        assert notifications[0]["status"] == "completed"

    @pytest.mark.asyncio
    async def test_send_failure_notification(self):
        """Test sending failure notification."""
        from src.api.services.notification import NotificationService
        from src.api.models.job import JobStatus

        notification_service = NotificationService()

        # Create mock failed job
        mock_job = Mock()
        mock_job.id = str(uuid4())
        mock_job.status = JobStatus.failed
        mock_job.progress = 45.0
        mock_job.error_message = "Connection timeout"
        mock_job.created_by = 1
        mock_job.workflow_id = 123

        # Mock user
        mock_user = Mock()
        mock_user.id = 1
        mock_user.email = "user@example.com"

        # Send failure notification
        await notification_service.send_failure_notification(mock_job, mock_user)

        # Verify notification
        notifications = notification_service.get_notifications(mock_user.id)
        assert len(notifications) == 1
        assert notifications[0]["type"] == "job_failed"
        assert "error" in notifications[0]  # Check error key exists

    @pytest.mark.asyncio
    async def test_send_progress_update(self):
        """Test sending progress update notification."""
        from src.api.services.notification import NotificationService

        notification_service = NotificationService()

        # Create mock job
        mock_job = Mock()
        mock_job.id = str(uuid4())
        mock_job.progress = 50.0
        mock_job.created_by = 1

        # Mock user
        mock_user = Mock()
        mock_user.id = 1

        # Send progress update
        await notification_service.send_progress_update(mock_job, mock_user, 50.0)

        # Verify notification
        notifications = notification_service.get_notifications(mock_user.id)
        assert len(notifications) == 1
        assert notifications[0]["type"] == "job_progress"
        assert notifications[0]["progress"] == 50.0


class TestJobStatusTracking:
    """Test job status tracking integration."""

    @pytest.mark.asyncio
    async def test_job_status_queryable_by_id(self):
        """Test that job status can be queried by ID."""
        from src.api.services.job import JobService
        from src.api.models.job import Job, JobStatus

        # Mock database session
        mock_db = AsyncMock()

        # Create mock job
        mock_job = Mock(spec=Job)
        mock_job.id = str(uuid4())
        mock_job.status = JobStatus.running
        mock_job.progress = 65.0
        mock_job.started_at = datetime.utcnow()
        mock_job.completed_at = None
        mock_job.error_message = None
        mock_job.result = None
        mock_job.workflow_id = 123
        mock_job.created_by = 1

        # Mock database query result
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_job
        mock_db.execute.return_value = mock_result

        # Create job service
        job_service = JobService(mock_db)

        # Query job status
        job = await job_service.get_job(mock_job.id, owner_id=1)

        # Verify job status is accessible
        assert job is not None
        assert job.status == JobStatus.running
        assert job.progress == 65.0

    @pytest.mark.asyncio
    async def test_progress_percentage_tracked(self):
        """Test that progress percentage is tracked."""
        from src.api.services.job import JobService
        from src.api.models.job import Job, JobStatus

        mock_db = AsyncMock()

        # Create job with progress
        mock_job = Mock(spec=Job)
        mock_job.id = str(uuid4())
        mock_job.status = JobStatus.running
        mock_job.progress = 75.5
        mock_job.started_at = datetime.utcnow()
        mock_job.completed_at = None
        mock_job.error_message = None
        mock_job.result = None
        mock_job.workflow_id = 123
        mock_job.created_by = 1

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_job
        mock_db.execute.return_value = mock_result

        job_service = JobService(mock_db)

        # Query job
        job = await job_service.get_job(mock_job.id, owner_id=1)

        # Verify progress is tracked
        assert job.progress == 75.5

    @pytest.mark.asyncio
    async def test_error_state_preserved_with_details(self):
        """Test that error state is preserved with error details."""
        from src.api.services.job import JobService
        from src.api.models.job import Job, JobStatus

        mock_db = AsyncMock()

        # Create failed job
        mock_job = Mock(spec=Job)
        mock_job.id = str(uuid4())
        mock_job.status = JobStatus.failed
        mock_job.progress = 30.0
        mock_job.started_at = datetime.utcnow()
        mock_job.completed_at = datetime.utcnow()
        mock_job.error_message = "ConnectionError: Database timeout after 30s"
        mock_job.result = None
        mock_job.workflow_id = 123
        mock_job.created_by = 1

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_job
        mock_db.execute.return_value = mock_result

        job_service = JobService(mock_db)

        # Query failed job
        job = await job_service.get_job(mock_job.id, owner_id=1)

        # Verify error details are preserved
        assert job.status == JobStatus.failed
        assert job.error_message == "ConnectionError: Database timeout after 30s"
        assert job.progress == 30.0

    @pytest.mark.asyncio
    async def test_completion_notification_sent(self):
        """Test that completion notification is sent."""
        from src.api.services.job import JobService
        from src.api.services.notification import NotificationService
        from src.api.models.job import Job, JobStatus
        from unittest.mock import MagicMock

        mock_db = AsyncMock()

        # Mock user
        mock_user = Mock()
        mock_user.id = 1
        mock_user.email = "user@example.com"

        # Create completed job
        mock_job = Mock(spec=Job)
        mock_job.id = str(uuid4())
        mock_job.status = JobStatus.completed
        mock_job.progress = 100.0
        mock_job.started_at = datetime.utcnow()
        mock_job.completed_at = datetime.utcnow()
        mock_job.error_message = None
        mock_job.result = {"row_count": 5000}
        mock_job.workflow_id = 123
        mock_job.created_by = 1

        # Mock the join query result that returns (Job, User) tuple
        mock_row = Mock()
        mock_row.__iter__ = lambda self: iter([mock_job, mock_user])

        mock_result = Mock()
        mock_result.first.return_value = mock_row
        mock_db.execute.return_value = mock_result

        job_service = JobService(mock_db)

        # Mock notification service
        with patch('src.api.services.notification.get_notification_service') as mock_get_service:
            mock_notification_service = AsyncMock()
            mock_get_service.return_value = mock_notification_service

            # Update job status to completed
            await job_service.update_job_status(
                mock_job.id,
                JobStatus.completed,
                progress=100.0,
                result={"row_count": 5000}
            )

            # Verify notification was called
            assert mock_notification_service.send_completion_notification.called


class TestNotificationRetrieval:
    """Test notification retrieval API."""

    @pytest.mark.asyncio
    async def test_get_user_notifications(self):
        """Test retrieving notifications for a user."""
        from src.api.services.notification import NotificationService

        notification_service = NotificationService()

        # Add multiple notifications
        user_id = 1
        for i in range(3):
            await notification_service.send_progress_update(
                Mock(id=str(uuid4()), created_by=user_id),
                Mock(id=user_id),
                i * 25.0
            )

        # Get notifications
        notifications = notification_service.get_notifications(user_id)

        assert len(notifications) == 3

    @pytest.mark.asyncio
    async def test_clear_notifications(self):
        """Test clearing notifications for a user."""
        from src.api.services.notification import NotificationService

        notification_service = NotificationService()

        user_id = 1
        mock_job = Mock(id=str(uuid4()), created_by=user_id)
        mock_user = Mock(id=user_id)

        # Add notifications
        await notification_service.send_progress_update(mock_job, mock_user, 50.0)

        # Clear notifications
        notification_service.clear_notifications(user_id)

        # Verify cleared
        notifications = notification_service.get_notifications(user_id)
        assert len(notifications) == 0

    @pytest.mark.asyncio
    async def test_notification_pagination(self):
        """Test notification pagination."""
        from src.api.services.notification import NotificationService

        notification_service = NotificationService()

        user_id = 1
        mock_job = Mock(id=str(uuid4()), created_by=user_id)
        mock_user = Mock(id=user_id)

        # Add many notifications
        for i in range(15):
            await notification_service.send_progress_update(
                mock_job, mock_user, i * 5.0
            )

        # Get paginated notifications
        notifications = notification_service.get_notifications(user_id, limit=10)

        assert len(notifications) == 10
