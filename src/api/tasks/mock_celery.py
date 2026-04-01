"""
Celery Mock for Testing

Mock Celery implementation for TDD development without broker dependency.
This allows testing task logic without requiring Redis/RabbitMQ setup.
"""

from typing import Callable, Any, Optional
from functools import wraps


class MockCeleryApp:
    """Mock Celery app for testing."""

    def __init__(self, main_name: str, broker: str = 'memory://', **kwargs):
        self.main = main_name
        self.conf = {}
        self.tasks = {}
        self._task_registry = {}

    def update(self, **kwargs):
        """Update configuration."""
        self.conf.update(kwargs)

    def register_task(self, name: str, task: 'MockTask'):
        """Register a task with the app."""
        self._task_registry[name] = task

    def __getattr__(self, name: str):
        """Allow accessing tasks as attributes."""
        if name in self._task_registry:
            return self._task_registry[name]
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    def __dir__(self):
        """Include registered tasks in dir() output."""
        default_dir = super().__dir__() if hasattr(super(), '__dir__') else []
        return default_dir + list(self._task_registry.keys())


class MockTask:
    """Mock Celery task for testing."""

    def __init__(self, func: Callable, **kwargs):
        self.func = func
        self.name = kwargs.get('name', func.__name__)
        self.priority = kwargs.get('priority', 5)
        self.autoretry_for = kwargs.get('autoretry_for', ())
        self.retry_kwargs = kwargs.get('retry_kwargs', {})
        self.retry_backoff = kwargs.get('retry_backoff', False)
        self.retry_backoff_max = kwargs.get('retry_backoff_max', 600)
        self.retry_jitter = kwargs.get('retry_jitter', False)
        self.time_limit = kwargs.get('time_limit', 3600)
        self.bind = kwargs.get('bind', False)
        self._instance = None  # For bound tasks

    def __call__(self, *args, **kwargs):
        """Execute task synchronously."""
        if self.bind:
            # Insert self as first argument
            args = (self,) + args
        return self.func(*args, **kwargs)

    def apply_async(self, args=None, kwargs=None, priority=None):
        """Mock apply_async - executes task synchronously and returns a mock result."""
        class MockAsyncResult:
            def __init__(self, result):
                self.result = result
                self.id = "mock-task-id"
                self.status = "SUCCESS"

        # Execute with provided args and kwargs
        # For bound tasks, insert self as first argument
        call_args = list(args or ())
        if self.bind:
            call_args = [self] + call_args

        result = self.func(*call_args, **kwargs or {})
        return MockAsyncResult(result)


def shared_task(**kwargs):
    """Mock shared_task decorator."""
    def decorator(func: Callable) -> MockTask:
        return MockTask(func, **kwargs)
    return decorator


def Celery(main_name: str, **kwargs):
    """Mock Celery constructor."""
    return MockCeleryApp(main_name, **kwargs)


# Mock celery app
celery_app = Celery('duckdb_processor', broker='memory://')

