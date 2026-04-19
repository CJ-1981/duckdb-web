"""
Dependency Injection Module

Provides dependency injection functions for FastAPI endpoints.
"""

from typing import Optional, Generator
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.processor import Processor
from src.core.config.loader import Config
from src.api.services.users import UserService


# Singleton instances
_processor_instance: Optional[Processor] = None
_config_instance: Optional[Config] = None


def get_processor() -> Generator[Processor, None, None]:
    """
    Provide Processor instance via dependency injection.

    Uses singleton pattern to avoid creating multiple processor instances.

    Yields:
        Processor: Configured processor instance
    """
    global _processor_instance

    if _processor_instance is None:
        # Create processor with default configuration
        _processor_instance = Processor()

    yield _processor_instance


def get_config() -> Generator[Config, None, None]:
    """
    Provide Config instance via dependency injection.

    Uses singleton pattern to avoid loading config multiple times.

    Yields:
        Config: Loaded configuration instance
    """
    global _config_instance

    if _config_instance is None:
        # Try to load from default config path
        try:
            _config_instance = Config("config.yaml")
            _config_instance.load()
        except FileNotFoundError:
            # Create default config if file doesn't exist
            _config_instance = _create_default_config()

    yield _config_instance


def _create_default_config() -> Config:
    """
    Create default configuration when config file not found.

    Returns:
        Config: Default configuration instance
    """
    from unittest.mock import Mock

    mock_config = Mock()
    mock_config.api = Mock()
    mock_config.api.title = "DuckDB Data Processor API"
    mock_config.api.version = "1.0.0"
    mock_config.api.host = "0.0.0.0"
    mock_config.api.port = 8000
    mock_config.api.debug = False
    mock_config.api.cors = Mock()
    mock_config.api.cors.allow_origins = ["http://localhost:3000"]
    mock_config.api.cors.allow_credentials = True
    mock_config.api.cors.allow_methods = ["*"]
    mock_config.api.cors.allow_headers = ["*"]
    mock_config.api.openapi = Mock()
    mock_config.api.openapi.enabled = True
    mock_config.api.openapi.swagger_path = "/docs"
    mock_config.api.openapi.redoc_path = "/redoc"
    mock_config.get = lambda key, default=None: default

    return mock_config


def reset_dependencies():
    """
    Reset singleton instances (useful for testing).

    Clears cached instances to force fresh creation.
    """
    global _processor_instance, _config_instance
    _processor_instance = None
    _config_instance = None


from fastapi import Depends
from src.api.models.base import get_async_session


async def get_db():
    """
    Provide async database session via dependency injection.

    Override this in tests with app.dependency_overrides[get_db].

    Yields:
        AsyncSession: Database session
    """
    async for session in get_async_session():
        yield session


def get_user_service(db: AsyncSession = Depends(get_async_session)) -> UserService:
    """
    Provide UserService instance via dependency injection.

    Args:
        db: Database session

    Returns:
        UserService: User service instance

    @MX:ANCHOR: UserService dependency injection (fan_in >= 3: user routes, auth, tests)
    """
    return UserService(db)


def get_current_user():
    """
    Get current authenticated user.

    Returns:
        Current user object

    @MX:TODO: Implement JWT authentication (P2-T002)
    """
    # Mock implementation for now
    from unittest.mock import Mock
    mock_user = Mock()
    mock_user.id = 1
    mock_user.username = "testuser"
    mock_user.email = "test@example.com"
    mock_user.is_admin = True
    return mock_user

