"""
Session management for CSV file uploads.

This module provides in-memory session storage with automatic cleanup,
supporting up to 10 concurrent sessions with 30-minute timeouts.
"""

import threading
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


# @MX:ANCHOR: [AUTO] Session Manager class for CSV file upload sessions
# @MX:REASON: Core session lifecycle management with 30-minute timeout and 10-session limit
# @MX:SPEC: SPEC-CSV-001 AC-CSV-008, AC-CSV-009
class SessionManager:
    """
    Manages in-memory sessions for uploaded CSV files.

    Provides thread-safe session storage with automatic expiration based on
    inactivity timeout. Supports up to 10 concurrent sessions with UUID v4
    identifiers.

    Attributes:
        max_sessions: Maximum number of concurrent sessions (default: 10)
        session_timeout: Session timeout duration (default: 30 minutes)
        _sessions: Internal session storage dictionary
        _lock: Thread lock for concurrent access protection
    """

    def __init__(self, max_sessions: int = 10, session_timeout_minutes: int = 30):
        """
        Initialize session manager.

        Args:
            max_sessions: Maximum concurrent sessions (default: 10)
            session_timeout_minutes: Session timeout in minutes (default: 30)

        Raises:
            ValueError: If max_sessions is less than 1 or timeout is negative
        """
        if max_sessions < 1:
            raise ValueError("max_sessions must be at least 1")
        if session_timeout_minutes < 0:
            raise ValueError("session_timeout_minutes cannot be negative")

        self.max_sessions = max_sessions
        self.session_timeout = timedelta(minutes=session_timeout_minutes)
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

        logger.info(
            f">>> [SESSION MANAGER] Initialized with max_sessions={max_sessions}, "
            f"timeout={session_timeout_minutes}min"
        )

    def create_session(self, file_data: Dict[str, Any]) -> str:
        """
        Create a new session with unique UUID v4 identifier.

        Stores file metadata and content with creation and last access timestamps.
        Automatically rejects new sessions when maximum concurrent limit reached.

        Args:
            file_data: Dictionary containing file metadata:
                - filename: Original filename (sanitized)
                - encoding: Detected character encoding
                - row_count: Total number of rows
                - column_count: Total number of columns
                - schema: Inferred column schema (list of dicts)
                - filepath: Path to uploaded file (optional)

        Returns:
            session_id: UUID v4 string

        Raises:
            RuntimeError: If maximum concurrent sessions reached
            ValueError: If required file_data fields are missing
        """
        # Validate required fields
        required_fields = ['filename', 'encoding', 'row_count', 'column_count', 'schema']
        missing_fields = [f for f in required_fields if f not in file_data]
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

        with self._lock:
            # Check session limit
            active_count = len(self._sessions)
            if active_count >= self.max_sessions:
                logger.warning(
                    f">>> [SESSION MANAGER] Max sessions reached ({self.max_sessions}), "
                    f"rejecting new session"
                )
                raise RuntimeError(
                    f"Maximum concurrent sessions ({self.max_sessions}) reached. "
                    f"Please wait for existing sessions to expire."
                )

            # Generate unique session ID
            session_id = str(uuid.uuid4())
            now = datetime.now()

            # Create session record
            session = {
                'session_id': session_id,
                'filename': file_data['filename'],
                'encoding': file_data['encoding'],
                'row_count': file_data['row_count'],
                'column_count': file_data['column_count'],
                'schema': file_data['schema'],
                'filepath': file_data.get('filepath'),
                'created_at': now,
                'last_access': now
            }

            # Store session
            self._sessions[session_id] = session

            logger.info(
                f">>> [SESSION MANAGER] Created session {session_id} "
                f"({active_count + 1}/{self.max_sessions} active)"
            )

            return session_id

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve session data by ID, updating last access timestamp.

        Automatically checks session expiration and returns None for expired
        or non-existent sessions. Updates last_access timestamp on successful
        retrieval to extend session lifetime.

        Args:
            session_id: UUID v4 string

        Returns:
            Session data dictionary or None if not found/expired

        Example:
            >>> session = manager.get_session('abc-123-def')
            >>> if session:
            ...     print(session['filename'], session['encoding'])
        """
        with self._lock:
            session = self._sessions.get(session_id)

            if session is None:
                logger.debug(f">>> [SESSION MANAGER] Session not found: {session_id}")
                return None

            # Check expiration
            now = datetime.now()
            time_since_access = now - session['last_access']

            if time_since_access > self.session_timeout:
                logger.info(
                    f">>> [SESSION MANAGER] Session expired: {session_id} "
                    f"(inactive for {time_since_access.total_seconds():.0f}s)"
                )
                # Remove expired session
                del self._sessions[session_id]
                return None

            # Update last access timestamp
            session['last_access'] = now
            return session.copy()  # Return copy to prevent external mutation

    def cleanup_expired_sessions(self) -> int:
        """
        Remove all sessions that have exceeded the timeout period.

        This method should be called periodically (e.g., via background task)
        to free memory from inactive sessions. Thread-safe and can be called
        concurrently with other operations.

        Returns:
            Number of sessions removed

        Example:
            >>> removed = manager.cleanup_expired_sessions()
            >>> print(f"Cleaned up {removed} expired sessions")
        """
        with self._lock:
            now = datetime.now()
            expired_ids = []

            # Find expired sessions
            for session_id, session in self._sessions.items():
                time_since_access = now - session['last_access']
                if time_since_access > self.session_timeout:
                    expired_ids.append(session_id)

            # Remove expired sessions
            for session_id in expired_ids:
                del self._sessions[session_id]

            if expired_ids:
                logger.info(
                    f">>> [SESSION MANAGER] Cleaned up {len(expired_ids)} expired sessions"
                )

            return len(expired_ids)

    def get_active_count(self) -> int:
        """
        Get current number of active sessions.

        Returns:
            Number of sessions currently stored (includes expired sessions
            until cleanup is called)
        """
        with self._lock:
            return len(self._sessions)


__all__ = ['SessionManager']
