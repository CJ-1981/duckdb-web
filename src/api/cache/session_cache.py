"""
Session Cache

Session data caching with automatic expiration.
Used for JWT session management and user state.

@MX:SPEC: SPEC-PLATFORM-001 P2-T009
"""

from typing import Any, Optional, Dict
from .manager import CacheManager


class SessionCache:
    """
    Session data cache with TTL-based expiration.

    Provides fast session storage with automatic cleanup
    after expiration.

    Attributes:
        redis: Redis client
        manager: Cache manager instance
        default_ttl: Default session TTL (3600 seconds = 1 hour)

    @MX:NOTE: Sessions cached to reduce database load for frequent auth checks
    """

    def __init__(self, redis_client: Any, default_ttl: int = 3600):
        """
        Initialize session cache.

        Args:
            redis_client: Redis client instance
            default_ttl: Default TTL in seconds (default: 1 hour)
        """
        self.redis = redis_client
        self.manager = CacheManager(redis_client)
        self.default_ttl = default_ttl

    async def set(self, session_id: str, session_data: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """
        Store session data.

        Args:
            session_id: Unique session identifier
            session_data: Session data dictionary
            ttl: Override default TTL

        Returns:
            True if stored successfully
        """
        # Generate cache key
        cache_key = self._generate_cache_key(session_id)

        # Set with TTL
        ttl = ttl or self.default_ttl
        return await self.manager.set(cache_key, session_data, ttl=ttl)

    async def get(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve session data.

        Args:
            session_id: Unique session identifier

        Returns:
            Session data or None if not found/expired
        """
        cache_key = self._generate_cache_key(session_id)
        return await self.manager.get(cache_key)

    async def delete(self, session_id: str) -> bool:
        """
        Delete a session (logout).

        Args:
            session_id: Session to delete

        Returns:
            True if deleted successfully
        """
        cache_key = self._generate_cache_key(session_id)
        return await self.manager.delete(cache_key)

    async def refresh(self, session_id: str, ttl: Optional[int] = None) -> bool:
        """
        Refresh session TTL (keep-alive).

        Args:
            session_id: Session to refresh
            ttl: New TTL (uses default if not specified)

        Returns:
            True if refreshed successfully

        @MX:NOTE: Called on authenticated requests to extend session
        """
        # Get existing session data
        session_data = await self.get(session_id)

        if session_data is None:
            return False

        # Reset with new TTL
        return await self.set(session_id, session_data, ttl=ttl)

    def _generate_cache_key(self, session_id: str) -> str:
        """
        Generate cache key for session.

        Args:
            session_id: Session identifier

        Returns:
            Cache key with "session:" prefix
        """
        return self.manager.generate_key("session", session_id)

    async def get_active_sessions(self, user_id: int) -> list:
        """
        Get all active sessions for a user.

        Args:
            user_id: User ID

        Returns:
            List of session IDs

        @MX:TODO: Implement user->session mapping for multi-device support
        """
        # Simplified: scan all session keys
        # In production, maintain user->sessions set
        pattern = "session:*"
        sessions = []

        async for key in self.redis.scan_iter(match=pattern):
            # Check if session belongs to user
            session_data = await self.manager.get(key.decode())
            if session_data and session_data.get("user_id") == user_id:
                sessions.append(key.decode().split(":")[-1])

        return sessions


__all__ = ['SessionCache']
