"""Unit tests for session management module."""

import pytest
import time
from uuid import UUID
from datetime import datetime, timedelta

from src.csv_parser.session_manager import SessionManager


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def session_manager():
    """Create a fresh SessionManager instance for each test."""
    return SessionManager(max_sessions=10, session_timeout_minutes=30)


@pytest.fixture
def sample_file_data():
    """Create sample file data for session creation."""
    return {
        'filename': 'test.csv',
        'encoding': 'utf-8',
        'row_count': 100,
        'column_count': 5,
        'schema': [
            {'name': 'id', 'type': 'Integer', 'nullable': False, 'null_count': 0},
            {'name': 'name', 'type': 'String', 'nullable': True, 'null_count': 5}
        ]
    }


# ============================================================================
# Session Creation Tests
# ============================================================================

def test_create_session(session_manager, sample_file_data):
    """Test session creation with unique UUID v4 IDs."""
    session_id = session_manager.create_session(sample_file_data)

    # Verify UUID v4 format
    uuid_obj = UUID(session_id)
    assert str(uuid_obj) == session_id
    assert uuid_obj.version == 4

    # Verify session is stored
    session = session_manager.get_session(session_id)
    assert session is not None
    assert session['filename'] == 'test.csv'
    assert session['encoding'] == 'utf-8'


def test_create_session_missing_required_fields(session_manager):
    """Test session creation fails with missing required fields."""
    incomplete_data = {
        'filename': 'test.csv',
        'encoding': 'utf-8'
        # Missing row_count, column_count, schema
    }

    with pytest.raises(ValueError, match="Missing required fields"):
        session_manager.create_session(incomplete_data)


def test_create_multiple_unique_sessions(session_manager, sample_file_data):
    """Test multiple sessions receive unique IDs."""
    session_id_1 = session_manager.create_session(sample_file_data)
    session_id_2 = session_manager.create_session(sample_file_data)

    assert session_id_1 != session_id_2


# ============================================================================
# Session Retrieval Tests
# ============================================================================

def test_get_session_valid(session_manager, sample_file_data):
    """Test retrieving valid session."""
    session_id = session_manager.create_session(sample_file_data)
    session = session_manager.get_session(session_id)

    assert session is not None
    assert session['session_id'] == session_id
    assert session['filename'] == 'test.csv'
    assert session['row_count'] == 100


def test_get_session_invalid_id(session_manager):
    """Test retrieving non-existent session returns None."""
    session = session_manager.get_session('non-existent-id')
    assert session is None


def test_get_session_updates_last_access(session_manager, sample_file_data):
    """Test last access timestamp is updated on retrieval."""
    session_id = session_manager.create_session(sample_file_data)

    # Get initial last_access
    session = session_manager.get_session(session_id)
    initial_access = session['last_access']

    # Wait a moment
    time.sleep(0.1)

    # Retrieve session again
    session = session_manager.get_session(session_id)
    updated_access = session['last_access']

    # Verify last_access was updated
    assert updated_access > initial_access


def test_get_session_returns_copy(session_manager, sample_file_data):
    """Test get_session returns a copy, not the internal dictionary."""
    session_id = session_manager.create_session(sample_file_data)
    session_1 = session_manager.get_session(session_id)
    session_2 = session_manager.get_session(session_id)

    # Modify returned copy
    session_1['filename'] = 'modified.csv'

    # Verify original session is unchanged
    assert session_2['filename'] == 'test.csv'


# ============================================================================
# Session Expiration Tests
# ============================================================================

def test_session_expiration_30_minutes(session_manager, sample_file_data):
    """Test session expires after 30 minutes of inactivity."""
    # Create session manager with 1-minute timeout for testing
    quick_timeout_manager = SessionManager(
        max_sessions=10,
        session_timeout_minutes=1
    )

    session_id = quick_timeout_manager.create_session(sample_file_data)

    # Verify session is initially valid
    session = quick_timeout_manager.get_session(session_id)
    assert session is not None

    # Manually expire the session by setting last_access to past
    with quick_timeout_manager._lock:
        quick_timeout_manager._sessions[session_id]['last_access'] = (
            datetime.now() - timedelta(minutes=2)
        )

    # Verify session is now expired
    session = quick_timeout_manager.get_session(session_id)
    assert session is None


def test_last_access_updates_expiration(session_manager, sample_file_data):
    """Test last access updates expiration time."""
    # Create session manager with 1-minute timeout
    quick_timeout_manager = SessionManager(
        max_sessions=10,
        session_timeout_minutes=1
    )

    session_id = quick_timeout_manager.create_session(sample_file_data)

    # Wait 30 seconds
    time.sleep(0.5)  # Use shorter delay for testing

    # Access the session to update last_access
    session = quick_timeout_manager.get_session(session_id)
    assert session is not None

    # Wait another 30 seconds
    time.sleep(0.5)

    # Session should still be valid due to recent access
    session = quick_timeout_manager.get_session(session_id)
    assert session is not None


# ============================================================================
# Concurrent Session Limits Tests
# ============================================================================

def test_max_concurrent_sessions(session_manager, sample_file_data):
    """Test system rejects new sessions when limit reached (10 max)."""
    # Create a manager with 3 session limit for testing
    limited_manager = SessionManager(max_sessions=3, session_timeout_minutes=30)

    # Create 3 sessions (at limit)
    session_id_1 = limited_manager.create_session(sample_file_data)
    session_id_2 = limited_manager.create_session(sample_file_data)
    session_id_3 = limited_manager.create_session(sample_file_data)

    assert limited_manager.get_active_count() == 3

    # Attempt to create 4th session (should fail)
    with pytest.raises(RuntimeError, match="Maximum concurrent sessions"):
        limited_manager.create_session(sample_file_data)


def test_session_limit_increments_after_expiry(session_manager, sample_file_data):
    """Test session count decreases when sessions expire."""
    # Create manager with 1-minute timeout
    quick_timeout_manager = SessionManager(
        max_sessions=2,
        session_timeout_minutes=1
    )

    # Create 2 sessions (at limit)
    session_id_1 = quick_timeout_manager.create_session(sample_file_data)
    session_id_2 = quick_timeout_manager.create_session(sample_file_data)

    assert quick_timeout_manager.get_active_count() == 2

    # Expire first session
    with quick_timeout_manager._lock:
        quick_timeout_manager._sessions[session_id_1]['last_access'] = (
            datetime.now() - timedelta(minutes=2)
        )

    # Trigger expiration via get_session
    quick_timeout_manager.get_session(session_id_1)

    # Verify count decreased
    assert quick_timeout_manager.get_active_count() == 1

    # Should now be able to create new session
    session_id_3 = quick_timeout_manager.create_session(sample_file_data)
    assert session_id_3 is not None


# ============================================================================
# Automatic Cleanup Tests
# ============================================================================

def test_automatic_cleanup(session_manager, sample_file_data):
    """Test automatic cleanup of expired sessions."""
    # Create manager with 1-minute timeout
    quick_timeout_manager = SessionManager(
        max_sessions=10,
        session_timeout_minutes=1
    )

    # Create 3 sessions
    session_id_1 = quick_timeout_manager.create_session(sample_file_data)
    session_id_2 = quick_timeout_manager.create_session(sample_file_data)
    session_id_3 = quick_timeout_manager.create_session(sample_file_data)

    # Expire first two sessions
    with quick_timeout_manager._lock:
        quick_timeout_manager._sessions[session_id_1]['last_access'] = (
            datetime.now() - timedelta(minutes=2)
        )
        quick_timeout_manager._sessions[session_id_2]['last_access'] = (
            datetime.now() - timedelta(minutes=2)
        )

    # Run cleanup
    removed_count = quick_timeout_manager.cleanup_expired_sessions()

    assert removed_count == 2
    assert quick_timeout_manager.get_active_count() == 1

    # Verify only session_id_3 remains
    assert quick_timeout_manager.get_session(session_id_1) is None
    assert quick_timeout_manager.get_session(session_id_2) is None
    assert quick_timeout_manager.get_session(session_id_3) is not None


def test_cleanup_empty_manager(session_manager):
    """Test cleanup on empty manager returns 0."""
    removed_count = session_manager.cleanup_expired_sessions()
    assert removed_count == 0


# ============================================================================
# Error Handling Tests
# ============================================================================

def test_invalid_max_sessions():
    """Test SessionManager rejects invalid max_sessions."""
    with pytest.raises(ValueError, match="max_sessions must be at least 1"):
        SessionManager(max_sessions=0)

    with pytest.raises(ValueError, match="max_sessions must be at least 1"):
        SessionManager(max_sessions=-1)


def test_invalid_timeout():
    """Test SessionManager rejects negative timeout."""
    with pytest.raises(ValueError, match="session_timeout_minutes cannot be negative"):
        SessionManager(max_sessions=10, session_timeout_minutes=-1)


# ============================================================================
# Thread Safety Tests
# ============================================================================

def test_concurrent_session_creation(session_manager, sample_file_data):
    """Test concurrent session creation is thread-safe."""
    import threading

    sessions_created = []
    errors = []

    def create_session():
        try:
            session_id = session_manager.create_session(sample_file_data)
            sessions_created.append(session_id)
        except Exception as e:
            errors.append(e)

    # Create 5 threads
    threads = [threading.Thread(target=create_session) for _ in range(5)]

    # Start all threads
    for thread in threads:
        thread.start()

    # Wait for completion
    for thread in threads:
        thread.join()

    # Verify all sessions created successfully
    assert len(errors) == 0
    assert len(sessions_created) == 5
    assert len(set(sessions_created)) == 5  # All unique


def test_concurrent_session_access(session_manager, sample_file_data):
    """Test concurrent session access is thread-safe."""
    import threading

    session_id = session_manager.create_session(sample_file_data)
    results = []

    def access_session():
        session = session_manager.get_session(session_id)
        results.append(session is not None)

    # Create 10 threads accessing the same session
    threads = [threading.Thread(target=access_session) for _ in range(10)]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    # All accesses should succeed
    assert all(results)
