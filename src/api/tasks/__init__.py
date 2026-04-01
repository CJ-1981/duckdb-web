"""
Celery Configuration

Celery app configuration for async task processing.
Uses mock Celery for TDD development without broker dependency.
"""

try:
    from celery import Celery
    CELERY_AVAILABLE = True
except ImportError:
    from src.api.tasks.mock_celery import Celery, shared_task, MockTask as Task
    CELERY_AVAILABLE = False

if CELERY_AVAILABLE:
    # Create real Celery app
    celery_app = Celery(
        'duckdb_processor',
        broker='memory://',  # In-memory broker for testing
        backend='cache+memory://',  # In-memory result backend for testing
        include=[
            'src.api.tasks.workflow',
            'src.api.tasks.export'
        ]
    )

    # Task configuration
    celery_app.conf.update(
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='UTC',
        enable_utc=True,
        task_track_started=True,
        task_time_limit=3600,  # 1 hour default
        task_soft_time_limit=3300,  # Soft limit 55 minutes
        task_acks_late=True,
        worker_prefetch_multiplier=4,
    )
else:
    # Use mock Celery for testing
    from src.api.tasks.mock_celery import celery_app


__all__ = ['celery_app', 'CELERY_AVAILABLE']
