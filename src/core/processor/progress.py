"""
Progress Tracking for Streaming Operations

Provides real-time progress tracking with callbacks and ETA estimation.
"""

import time
import threading
from typing import Optional, List, Callable
from dataclasses import dataclass, field
from enum import Enum


class Operation(Enum):
    """Current operation state"""
    IDLE = "idle"
    READING = "reading"
    PROCESSING = "processing"
    WRITING = "writing"


@dataclass
class ProgressInfo:
    """
    Progress information for streaming operations

    Tracks rows and bytes processed, calculates percentage and ETA.
    """
    rows_processed: int = 0
    bytes_processed: int = 0
    total_rows: Optional[int] = None
    total_bytes: Optional[int] = None
    percentage: float = 0.0
    eta_seconds: Optional[float] = None
    current_operation: str = "idle"
    elapsed_seconds: float = 0.0
    chunks_processed: int = 0

    def __post_init__(self):
        """Calculate derived fields"""
        if self.total_rows and self.total_rows > 0:
            self.percentage = (self.rows_processed / self.total_rows) * 100


class ProgressTracker:
    """
    Thread-safe progress tracker with callback support

    Features:
    - Thread-safe progress updates
    - Configurable callback interval
    - ETA estimation
    - Memory of progress history
    """

    def __init__(
        self,
        update_interval: int = 1000,
        total_rows: Optional[int] = None,
        total_bytes: Optional[int] = None,
    ):
        """
        Initialize progress tracker

        Args:
            update_interval: Minimum milliseconds between callback invocations
            total_rows: Total rows to process (if known)
            total_bytes: Total bytes to process (if known)
        """
        self.update_interval = update_interval
        self.total_rows = total_rows
        self.total_bytes = total_bytes

        # Current state
        self._rows_processed = 0
        self._bytes_processed = 0
        self._chunks_processed = 0
        self._current_operation = Operation.IDLE

        # Timing
        self._start_time: Optional[float] = None
        self._last_update_time = 0.0

        # Callbacks
        self._callbacks: List[Callable[[ProgressInfo], None]] = []
        self._lock = threading.RLock()

    @property
    def rows_processed(self) -> int:
        """Get rows processed"""
        with self._lock:
            return self._rows_processed

    @property
    def bytes_processed(self) -> int:
        """Get bytes processed"""
        with self._lock:
            return self._bytes_processed

    def start(self) -> None:
        """Start progress tracking"""
        with self._lock:
            self._start_time = time.time()
            self._current_operation = Operation.READING

    def update(
        self,
        rows_processed: int,
        bytes_processed: int,
        operation: Optional[str] = None,
    ) -> None:
        """
        Update progress with new data

        Args:
            rows_processed: Number of rows processed
            bytes_processed: Number of bytes processed
            operation: Current operation (optional)
        """
        with self._lock:
            self._rows_processed = rows_processed
            self._bytes_processed = bytes_processed
            self._chunks_processed += 1

            if operation:
                self._current_operation = Operation(operation)

            # Check if callback should be invoked
            current_time = time.time() * 1000  # Convert to milliseconds
            if current_time - self._last_update_time >= self.update_interval:
                self._check_callback()
                self._last_update_time = current_time

    def add_callback(self, callback: Callable[[ProgressInfo], None]) -> None:
        """
        Add a progress callback

        Args:
            callback: Function to call on progress updates
        """
        with self._lock:
            self._callbacks.append(callback)

    def remove_callback(self, callback: Callable[[ProgressInfo], None]) -> None:
        """
        Remove a progress callback

        Args:
            callback: Function to remove
        """
        with self._lock:
            if callback in self._callbacks:
                self._callbacks.remove(callback)

    def get_progress(self) -> ProgressInfo:
        """
        Get current progress information

        Returns:
            ProgressInfo with current state
        """
        with self._lock:
            elapsed = 0.0
            eta = None

            if self._start_time:
                elapsed = time.time() - self._start_time

                # Calculate ETA if we have total rows
                if self.total_rows and self._rows_processed > 0:
                    rate = self._rows_processed / elapsed
                    remaining_rows = self.total_rows - self._rows_processed
                    if rate > 0:
                        eta = remaining_rows / rate

            percentage = 0.0
            if self.total_rows and self.total_rows > 0:
                percentage = (self._rows_processed / self.total_rows) * 100

            return ProgressInfo(
                rows_processed=self._rows_processed,
                bytes_processed=self._bytes_processed,
                total_rows=self.total_rows,
                total_bytes=self.total_bytes,
                percentage=percentage,
                eta_seconds=eta,
                current_operation=self._current_operation.value,
                elapsed_seconds=elapsed,
                chunks_processed=self._chunks_processed,
            )

    def reset(self) -> None:
        """Reset progress tracking"""
        with self._lock:
            self._rows_processed = 0
            self._bytes_processed = 0
            self._chunks_processed = 0
            self._start_time = None
            self._current_operation = Operation.IDLE
            self._last_update_time = 0.0

    def _check_callback(self) -> None:
        """Invoke callbacks with current progress"""
        if not self._callbacks:
            return

        info = self.get_progress()
        for callback in self._callbacks:
            try:
                callback(info)
            except Exception:
                # Don't let callback errors propagate
                pass
