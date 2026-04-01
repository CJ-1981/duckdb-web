"""
Notification Service

Service for sending and managing job status notifications.
Supports in-memory storage for testing with extension points for
WebSocket, email, and other notification channels.

@MX:SPEC: SPEC-PLATFORM-001 P2-T008
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from collections import defaultdict
import asyncio


class NotificationService:
    """
    Service for managing job status notifications.

    Provides in-memory notification storage with hooks for
    external notification systems (WebSocket, email, etc.).

    Attributes:
        _notifications: In-memory storage per user_id
        _hooks: Callback functions for notification events

    @MX:NOTE: In-memory storage for development; use Redis for production
    """

    def __init__(self):
        """Initialize notification service."""
        self._notifications: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
        self._hooks: Dict[str, List[callable]] = defaultdict(list)

    async def send_completion_notification(
        self,
        job: Any,
        user: Any
    ) -> None:
        """
        Send job completion notification.

        Args:
            job: Job object with status, result, etc.
            user: User object to receive notification

        @MX:ANCHOR: Completion notification delivery (fan_in >= 3: workflow task, export task, direct calls)
        """
        notification = {
            "id": f"notify_{job.id}_{datetime.utcnow().timestamp()}",
            "type": "job_completed",
            "job_id": job.id,
            "workflow_id": job.workflow_id,
            "status": job.status,
            "progress": job.progress,
            "result": job.result,
            "created_at": datetime.utcnow().isoformat(),
            "read": False
        }

        # Store notification
        self._notifications[user.id].append(notification)

        # Trigger hooks
        await self._trigger_hooks("job_completed", notification, user)

    async def send_failure_notification(
        self,
        job: Any,
        user: Any
    ) -> None:
        """
        Send job failure notification.

        Args:
            job: Job object with error details
            user: User object to receive notification
        """
        notification = {
            "id": f"notify_{job.id}_{datetime.utcnow().timestamp()}",
            "type": "job_failed",
            "job_id": job.id,
            "workflow_id": job.workflow_id,
            "status": job.status,
            "progress": job.progress,
            "error": job.error_message,
            "created_at": datetime.utcnow().isoformat(),
            "read": False
        }

        # Store notification
        self._notifications[user.id].append(notification)

        # Trigger hooks
        await self._trigger_hooks("job_failed", notification, user)

    async def send_progress_update(
        self,
        job: Any,
        user: Any,
        progress: float
    ) -> None:
        """
        Send job progress update notification.

        Args:
            job: Job object
            user: User object to receive notification
            progress: Progress percentage (0-100)
        """
        notification = {
            "id": f"notify_{job.id}_{datetime.utcnow().timestamp()}",
            "type": "job_progress",
            "job_id": job.id,
            "workflow_id": job.workflow_id,
            "progress": progress,
            "created_at": datetime.utcnow().isoformat(),
            "read": False
        }

        # Store notification
        self._notifications[user.id].append(notification)

        # Trigger hooks
        await self._trigger_hooks("job_progress", notification, user)

    def get_notifications(
        self,
        user_id: int,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve notifications for a user.

        Args:
            user_id: User ID to get notifications for
            limit: Maximum number of notifications to return

        Returns:
            List of notification dictionaries
        """
        notifications = self._notifications.get(user_id, [])

        # Sort by created_at descending
        notifications = sorted(
            notifications,
            key=lambda n: n["created_at"],
            reverse=True
        )

        if limit:
            notifications = notifications[:limit]

        return notifications

    def clear_notifications(self, user_id: int) -> None:
        """
        Clear all notifications for a user.

        Args:
            user_id: User ID to clear notifications for
        """
        if user_id in self._notifications:
            self._notifications[user_id].clear()

    def mark_as_read(self, user_id: int, notification_id: str) -> bool:
        """
        Mark a notification as read.

        Args:
            user_id: User ID
            notification_id: Notification ID to mark as read

        Returns:
            True if notification was found and marked, False otherwise
        """
        for notification in self._notifications.get(user_id, []):
            if notification["id"] == notification_id:
                notification["read"] = True
                return True
        return False

    def register_hook(self, event_type: str, callback: callable) -> None:
        """
        Register a callback hook for notification events.

        Args:
            event_type: Event type (e.g., "job_completed", "job_failed")
            callback: Async callback function

        @MX:TODO: Implement WebSocket hook for real-time notifications (P2-T008 enhancement)
        """
        self._hooks[event_type].append(callback)

    async def _trigger_hooks(
        self,
        event_type: str,
        notification: Dict[str, Any],
        user: Any
    ) -> None:
        """
        Trigger all registered hooks for an event type.

        Args:
            event_type: Event type
            notification: Notification data
            user: User object
        """
        hooks = self._hooks.get(event_type, [])

        # Execute all hooks concurrently
        if hooks:
            await asyncio.gather(
                *[hook(notification, user) for hook in hooks],
                return_exceptions=True
            )


# Global notification service instance
_notification_service: Optional[NotificationService] = None


def get_notification_service() -> NotificationService:
    """
    Get or create the global notification service instance.

    Returns:
        NotificationService instance

    @MX:ANCHOR: Notification service singleton (fan_in >= 3: job routes, task modules, tests)
    """
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService()
    return _notification_service


__all__ = [
    'NotificationService',
    'get_notification_service'
]
