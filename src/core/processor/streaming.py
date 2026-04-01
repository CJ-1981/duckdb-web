"""
Result Streaming with Memory Management

Provides memory-aware streaming for large datasets with progress tracking,
state management (pause/resume/cancel), and automatic chunk size adjustment.
"""

import os
import time
import threading
import psutil
from enum import Enum
from typing import Iterator, List, Dict, Any, Optional
from dataclasses import dataclass

from ..database import DatabaseConnection
from .progress import ProgressTracker, Operation


class StreamingState(Enum):
    """Streaming operation states"""
    IDLE = "idle"
    STREAMING = "streaming"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class StreamProcessor:
    """
    Memory-aware stream processor for large datasets

    Features:
    - Chunk-based streaming with configurable chunk size
    - Memory monitoring and enforcement
    - Progress tracking with callbacks
    - State management (pause, resume, cancel)
    - Automatic chunk size adjustment based on memory
    """

    def __init__(
        self,
        db_connection: DatabaseConnection,
        memory_limit_mb: int = 512,
        chunk_size: int = 10000,
        progress_update_interval: int = 1000,
        auto_adjust_chunk_size: bool = True,
    ):
        """
        Initialize stream processor

        Args:
            db_connection: Database connection to stream from
            memory_limit_mb: Memory limit in megabytes
            chunk_size: Initial chunk size (rows per chunk)
            progress_update_interval: Progress callback interval in milliseconds
            auto_adjust_chunk_size: Automatically reduce chunk size if memory limit approached
        """
        self.db_connection = db_connection
        self.memory_limit_mb = memory_limit_mb
        self.chunk_size = chunk_size
        self.progress_update_interval = progress_update_interval
        self.auto_adjust_chunk_size = auto_adjust_chunk_size

        # State management
        self._state = StreamingState.IDLE
        self._state_lock = threading.RLock()
        self._pause_event = threading.Event()
        self._cancel_event = threading.Event()

        # Progress tracking
        self.progress_tracker = ProgressTracker(
            update_interval=progress_update_interval
        )

    @property
    def state(self) -> StreamingState:
        """Get current streaming state"""
        with self._state_lock:
            return self._state

    @property
    def memory_limit_bytes(self) -> int:
        """Get memory limit in bytes"""
        return self.memory_limit_mb * 1024 * 1024

    def stream_query(
        self,
        query: str,
        parameters: Optional[List[Any]] = None,
    ) -> Iterator[List[Dict[str, Any]]]:
        """
        Stream query results in chunks with memory management

        Args:
            query: SQL query to execute
            parameters: Query parameters

        Yields:
            List of dictionaries (chunks)

        Raises:
            MemoryError: If memory limit exceeded
            RuntimeError: If query execution fails
        """
        # Reset state for new query
        self._cancel_event.clear()
        self._pause_event.clear()

        with self._state_lock:
            self._state = StreamingState.STREAMING

        self.progress_tracker.reset()
        self.progress_tracker.start()

        try:
            # Stream from database
            rows_processed = 0
            bytes_processed = 0

            for chunk in self.db_connection.stream(query, parameters or [], self.chunk_size):
                # Check for cancellation
                if self._cancel_event.is_set():
                    with self._state_lock:
                        self._state = StreamingState.CANCELLED
                    return

                # Check for pause
                self._pause_event.wait()

                # Memory check
                self._check_memory()

                # Calculate chunk size in bytes (rough estimate)
                chunk_bytes = self._estimate_chunk_bytes(chunk)
                bytes_processed += chunk_bytes
                rows_processed += len(chunk)

                # Update progress
                self.progress_tracker.update(
                    rows_processed=rows_processed,
                    bytes_processed=bytes_processed,
                    operation="reading",
                )

                yield chunk

                # Adjust chunk size if needed
                if self.auto_adjust_chunk_size:
                    self._adjust_chunk_size()

        except Exception as e:
            # Reset state on error
            with self._state_lock:
                self._state = StreamingState.IDLE
            raise
        finally:
            # Reset state on completion
            with self._state_lock:
                if self._state == StreamingState.STREAMING:
                    self._state = StreamingState.IDLE

    def pause(self) -> None:
        """
        Pause streaming at next chunk boundary

        Raises:
            RuntimeError: If not in STREAMING state
        """
        with self._state_lock:
            if self._state == StreamingState.IDLE:
                raise RuntimeError("Cannot pause from IDLE state")
            self._state = StreamingState.PAUSED

        self._pause_event.clear()

    def resume(self) -> None:
        """
        Resume paused streaming

        Raises:
            RuntimeError: If not in PAUSED state
        """
        with self._state_lock:
            if self._state == StreamingState.STREAMING:
                raise RuntimeError("Cannot resume from STREAMING state")
            self._state = StreamingState.STREAMING

        self._pause_event.set()

    def cancel(self) -> None:
        """Cancel streaming and cleanup resources"""
        self._cancel_event.set()
        self._pause_event.set()  # Unpause if paused

        with self._state_lock:
            self._state = StreamingState.CANCELLED

    def _check_memory(self) -> None:
        """Check current memory usage and raise error if limit exceeded"""
        current_mb = self._get_current_memory_mb()

        if current_mb > self.memory_limit_mb:
            raise MemoryError(
                f"Memory limit exceeded: {current_mb}MB > {self.memory_limit_mb}MB"
            )

    def _get_current_memory_mb(self) -> float:
        """Get current process memory in megabytes"""
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / (1024 * 1024)

    def _estimate_chunk_bytes(self, chunk: List[Dict[str, Any]]) -> int:
        """
        Estimate memory size of a chunk

        Rough estimation based on row count and average row size.
        """
        if not chunk:
            return 0

        # Estimate average row size (rough approximation)
        # Each dict has overhead + string/numeric values
        avg_row_size = 100  # bytes per row (conservative estimate)
        return len(chunk) * avg_row_size

    def _adjust_chunk_size(self) -> None:
        """Adjust chunk size based on current memory usage"""
        current_mb = self._get_current_memory_mb()
        threshold = self.memory_limit_mb * 0.8  # 80% threshold

        if current_mb > threshold:
            # Reduce chunk size by 25%
            self.chunk_size = max(1000, int(self.chunk_size * 0.75))
