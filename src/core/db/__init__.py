"""
Database connection management for SPEC-WORKFLOW-001

Provides:
- Database connection configuration
- Session management
- Async support
- Migration utilities
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from contextlib import asynccontextmanager, contextmanager
from typing import AsyncGenerator, Generator
import os

from .connection import Base

# Configuration - simplified for initial setup
SYNC_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./workflow.db")
ASYNC_DATABASE_URL = "sqlite+aiosqlite:///./workflow.db"

# Create engines
sync_engine = create_engine(
    SYNC_DATABASE_URL,
    pool_pre_ping=True,
    echo=False,
    future=True
)

async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    pool_pre_ping=True,
    echo=False,
    future=True
)

# Session makers
SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    class_=Session,
    expire_on_commit=False
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


@contextmanager
def get_sync_session() -> Generator[Session, None, None]:
    """Get synchronous database session"""
    session = SyncSessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@asynccontextmanager
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Get asynchronous database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def create_tables():
    """Create all database tables"""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_tables():
    """Drop all database tables"""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# Database utilities
def init_database():
    """Initialize database with tables"""
    try:
        # Create tables using sync engine for Alembic compatibility
        Base.metadata.create_all(bind=sync_engine)
        print("Database tables created successfully")
    except Exception as e:
        print(f"Error creating database tables: {e}")
        raise


def close_database():
    """Close database connections"""
    sync_engine.dispose()
    async_engine.dispose()
    print("Database connections closed")