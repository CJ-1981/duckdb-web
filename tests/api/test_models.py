"""
Database model tests.

Tests for SQLAlchemy models including User, Workflow, Job,
and their relationships.
"""

import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.api.models.user import User, UserRole
from src.api.models.workflow import Workflow
from src.api.models.job import Job, JobStatus


# ========================================================================
# Test Fixtures
# ========================================================================

@pytest.fixture
def in_memory_db():
    """Create in-memory SQLite database for testing."""
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.ext.asyncio import async_sessionmaker

    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False
    )

    async def get_session():
        async_session = async_sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
        async with async_session() as session:
            yield session

    return engine, get_session


# ========================================================================
# User Model Tests
# ========================================================================

class TestUserModel:
    """Test User model functionality."""

    def test_user_creation(self, in_memory_db):
        """Test creating a user instance."""
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password_here",
            role=UserRole.analyst
        )

        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.role == UserRole.analyst
        assert user.is_active is True

    def test_user_role_enum(self):
        """Test UserRole enum values."""
        assert UserRole.admin.value == "admin"
        assert UserRole.analyst.value == "analyst"
        assert UserRole.viewer.value == "viewer"

    def test_user_repr(self):
        """Test User string representation."""
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed",
            role=UserRole.viewer
        )
        user.id = 1

        repr_str = repr(user)
        assert "testuser" in repr_str
        assert "1" in repr_str

    def test_user_unique_constraints(self):
        """Test that user model has unique constraints."""
        # Check that the model defines unique constraints
        user_table = User.__table__
        username_column = user_table.columns['username']
        email_column = user_table.columns['email']

        assert username_column.unique
        assert email_column.unique


# ========================================================================
# Workflow Model Tests
# ========================================================================

class TestWorkflowModel:
    """Test Workflow model functionality."""

    def test_workflow_creation(self):
        """Test creating a workflow instance."""
        workflow = Workflow(
            name="Test Workflow",
            description="A test workflow",
            definition={"nodes": [], "edges": []},
            owner_id=1
        )

        assert workflow.name == "Test Workflow"
        assert workflow.description == "A test workflow"
        assert workflow.definition == {"nodes": [], "edges": []}
        assert workflow.owner_id == 1

    def test_workflow_relationships(self):
        """Test workflow relationships."""
        workflow = Workflow(
            name="Test Workflow",
            description="Test",
            definition={},
            owner_id=1
        )

        # Relationships should be defined
        assert hasattr(workflow, 'owner')
        assert hasattr(workflow, 'versions')
        assert hasattr(workflow, 'jobs')


# ========================================================================
# Job Model Tests
# ========================================================================

class TestJobModel:
    """Test Job model functionality."""

    def test_job_creation(self):
        """Test creating a job instance."""
        job = Job(
            workflow_id="test-workflow-id",
            status=JobStatus.pending,
            created_by=1
        )

        assert job.workflow_id == "test-workflow-id"
        assert job.status == JobStatus.pending
        assert job.created_by == 1

    def test_job_status_enum(self):
        """Test JobStatus enum values."""
        assert JobStatus.pending.value == "pending"
        assert JobStatus.running.value == "running"
        assert JobStatus.completed.value == "completed"
        assert JobStatus.failed.value == "failed"

    def test_job_status_transitions(self):
        """Test job status can transition properly."""
        job = Job(
            workflow_id="test",
            status=JobStatus.pending,
            created_by=1
        )

        # Pending -> Running
        job.status = JobStatus.running
        assert job.status == JobStatus.running

        # Running -> Completed
        job.status = JobStatus.completed
        assert job.status == JobStatus.completed


# ========================================================================
# Model Relationship Tests
# ========================================================================

class TestModelRelationships:
    """Test relationships between models."""

    def test_user_workflow_relationship(self):
        """Test User-Workflow relationship."""
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed",
            role=UserRole.analyst
        )
        user.id = 1

        workflow = Workflow(
            name="Test Workflow",
            description="Test",
            definition={},
            owner_id=user.id
        )

        assert workflow.owner_id == user.id

    def test_workflow_job_relationship(self):
        """Test Workflow-Job relationship."""
        workflow_id = "test-workflow-id"

        job = Job(
            workflow_id=workflow_id,
            status=JobStatus.pending,
            created_by=1
        )

        assert job.workflow_id == workflow_id

    def test_user_job_relationship(self):
        """Test User-Job relationship."""
        user_id = 1

        job = Job(
            workflow_id="test",
            status=JobStatus.pending,
            created_by=user_id
        )

        assert job.created_by == user_id


# ========================================================================
# Model Validation Tests
# ========================================================================

class TestModelValidation:
    """Test model validation and constraints."""

    def test_user_email_validation(self):
        """Test user model accepts valid email formats."""
        valid_emails = [
            "user@example.com",
            "user.name@example.com",
            "user+tag@example.co.uk"
        ]

        for email in valid_emails:
            user = User(
                username="testuser",
                email=email,
                password_hash="hashed",
                role=UserRole.viewer
            )
            assert user.email == email

    def test_user_username_length(self):
        """Test username length constraints."""
        # Valid username (within 3-50 characters)
        valid_username = "a" * 25
        user = User(
            username=valid_username,
            email="test@example.com",
            password_hash="hashed",
            role=UserRole.viewer
        )
        assert len(user.username) == 25

    def test_workflow_name_required(self):
        """Test workflow name is required."""
        with pytest.raises(Exception):
            workflow = Workflow(
                description="Test",
                definition={},
                owner_id=1
            )
            # This should fail due to NOT NULL constraint
            # (actual validation happens at database level)

    def test_job_status_default(self):
        """Test job status defaults to pending."""
        job = Job(
            workflow_id="test",
            created_by=1
        )

        assert job.status == JobStatus.pending
