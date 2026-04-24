"""
Pytest configuration and fixtures for integration tests.

@MX:NOTE: Shared fixtures for workflow execution tests
"""

import os
import sys
import tempfile
import pytest
import redis
from typing import AsyncGenerator, Generator
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from rq import Queue

from src.api.models.base import BaseModel
from src.api.models.job import Job, JobStatus
from src.api.models.workflow import Workflow
from src.api.models.user import User
from src.api.services.job import JobService


@pytest.fixture(scope="session")
def test_redis_url():
    """Get Redis URL for testing."""
    return os.getenv('REDIS_TEST_URL', 'redis://localhost:6379/1')


@pytest.fixture(scope="session")
def test_redis(test_redis_url: str) -> Generator[redis.Redis, None, None]:
    """Create Redis connection for testing."""
    client = redis.from_url(test_redis_url, decode_responses=False)

    # Flush test database before tests
    client.flushdb()

    yield client

    # Cleanup after tests
    client.flushdb()
    client.close()


@pytest.fixture(scope="session")
def test_database_url():
    """Get test database URL."""
    # Try to use PostgreSQL test database if available, otherwise use SQLite
    if os.getenv('POSTGRES_TEST_URL'):
        return os.getenv('POSTGRES_TEST_URL')
    return 'sqlite+aiosqlite:///:memory:'


@pytest.fixture(scope="function")
async def test_db_session(test_database_url: str) -> AsyncGenerator[AsyncSession, None]:
    """
    Create test database session.

    Creates all tables, yields session, then drops all tables.
    """
    # Create engine
    engine = create_async_engine(
        test_database_url,
        echo=False
    )

    # Create session maker
    async_session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)

    async with async_session_maker() as session:
        yield session

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def test_session_maker(test_database_url: str):
    """Create test session maker for workflow execution."""
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

    engine = create_async_engine(test_database_url, echo=False)
    async_session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)

    yield async_session_maker

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def test_user(test_db_session: AsyncSession) -> User:
    """Create test user."""
    from src.api.models.user import User
    from sqlalchemy import select

    # Check if user exists
    result = await test_db_session.execute(
        select(User).where(User.email == "test@example.com")
    )
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            email="test@example.com",
            username="testuser",
            password_hash="hashed_password_here"
        )
        test_db_session.add(user)
        await test_db_session.commit()
        await test_db_session.refresh(user)

    return user


@pytest.fixture
async def test_workflow(test_db_session: AsyncSession, test_user: User) -> Workflow:
    """Create test workflow."""
    from src.api.models.workflow import Workflow

    workflow = Workflow(
        name="Test Workflow",
        description="A test workflow for integration testing",
        definition={
            "nodes": [
                {
                    "id": "input_1",
                    "type": "input",
                    "data": {
                        "path": "tests/fixtures/test_data/workflow_samples/sample.csv",
                        "table_name": "input_table"
                    }
                },
                {
                    "id": "sql_1",
                    "type": "sql",
                    "data": {
                        "query": "SELECT COUNT(*) as row_count FROM input_table"
                    }
                },
                {
                    "id": "output_1",
                    "type": "output",
                    "data": {
                        "source": "sql_1"
                    }
                }
            ],
            "edges": [
                {"source": "input_1", "target": "sql_1"},
                {"source": "sql_1", "target": "output_1"}
            ]
        },
        owner_id=test_user.id
    )

    test_db_session.add(workflow)
    await test_db_session.commit()
    await test_db_session.refresh(workflow)

    return workflow


@pytest.fixture
def test_csv_file():
    """Create temporary CSV file for testing."""
    import csv

    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        writer = csv.writer(f)
        writer.writerow(['id', 'name', 'value'])
        writer.writerow([1, 'Alice', 100])
        writer.writerow([2, 'Bob', 200])
        writer.writerow([3, 'Charlie', 300])
        temp_path = f.name

    yield temp_path

    # Cleanup
    os.unlink(temp_path)


@pytest.fixture
def sample_workflow_definition(test_csv_file: str):
    """Create sample workflow definition for testing."""
    return {
        "nodes": [
            {
                "id": "input_1",
                "type": "input",
                "data": {
                    "path": test_csv_file,
                    "table_name": "test_input"
                }
            },
            {
                "id": "sql_1",
                "type": "sql",
                "data": {
                    "query": "SELECT COUNT(*) as row_count, SUM(value) as total_value FROM test_input"
                }
            },
            {
                "id": "output_1",
                "type": "output",
                "data": {
                    "source": "sql_1"
                }
            }
        ],
        "edges": [
            {"source": "input_1", "target": "sql_1"},
            {"source": "sql_1", "target": "output_1"}
        ]
    }


@pytest.fixture
def job_service(test_db_session: AsyncSession) -> JobService:
    """Create JobService instance."""
    return JobService(test_db_session)


@pytest.fixture
def rq_queue(test_redis: redis.Redis) -> Queue:
    """Create RQ queue for testing."""
    return Queue('spec_execution', connection=test_redis)
