"""
SQLAlchemy models package for the DuckDB Data Processor API.

This package exports all models and database session management utilities.
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

from .base import BaseModel
from .user import User, UserRole
from .workflow import Workflow
from .job import Job, JobStatus
from .workflow_version import WorkflowVersion

# Database configuration
# @MX:NOTE: Use environment variables in production
DATABASE_URL = "postgresql+asyncpg://user:pass@localhost/duckdb_processor"
TEST_DATABASE_URL = "sqlite+ai://sqlite:///:memory::testdb"

ASYNC_DATABASE_URL = DATABASE_URL

TEST_ASYNC_DATABASE_URL = TEST_DATABASE_URL

# Create declarative base
Base = declarative_base()
Base.metadata = BaseModel.metadata


# Database engine
engine = None
async_session_maker: async_sessionmaker | None = None


async def init_db(database_url: str = None) -> None:
    """
    Initialize database engine and session maker.

    Args:
        database_url: Database connection URL. If None, uses ASYNC_DATABASE_URL env var.
    """
    global engine, async_session_maker

    url = database_url or ASYNC_DATABASE_URL

    # Create async engine
    engine = create_async_engine(url, echo=False, pool_pre_ping=True)

    # Create session factory
    async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get async database session.

    Yields:
        AsyncSession instance

    Example:
        async with get_async_session() as session:
            async with session.begin():
                user = await session.execute(select(User).where(User.id == 1)).scalar_one()
    """
    if async_session_maker is None:
        await init_db()

    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def create_tables():
    """Create all database tables"""
    if engine is None:
        await init_db()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all(conn))


__all__ = [
    "BaseModel",
    "User",
    "UserRole",
    "Workflow",
    "Job",
    "JobStatus",
    "WorkflowVersion",
    "init_db",
    "get_async_session",
    "create_tables",
]
