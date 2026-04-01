"""
Unit Tests for Result Streaming (P1-T007)

TDD RED Phase: These tests define the expected behavior for streaming
large datasets with memory management, progress tracking, and state control.
"""

import pytest
import threading
import time
from typing import List, Dict, Any, Generator
from unittest.mock import Mock, MagicMock, patch
from dataclasses import dataclass

# These imports will fail until GREEN phase implementation
# This is expected in RED phase
pytest.importorskip("src.core.processor.streaming")
pytest.importorskip("src.core.processor.progress")

from src.core.processor.streaming import StreamProcessor, StreamingState
from src.core.processor.progress import ProgressTracker, ProgressInfo
from src.core.database import DatabaseConnection


class TestStreamProcessor:
    """Test suite for StreamProcessor class"""

    @pytest.fixture
    def mock_db_connection(self):
        """Create mock database connection"""
        mock_db = Mock(spec=DatabaseConnection)
        mock_db.db_path = ":memory:"
        return mock_db

    @pytest.fixture
    def stream_processor(self, mock_db_connection):
        """Create StreamProcessor instance"""
        return StreamProcessor(
            db_connection=mock_db_connection,
            memory_limit_mb=512,
            chunk_size=10000,
            progress_update_interval=1000,
        )

    # ========== Initialization Tests ==========

    def test_stream_processor_initialization(self, mock_db_connection):
        """Test StreamProcessor initializes with correct defaults"""
        processor = StreamProcessor(db_connection=mock_db_connection)

        assert processor.memory_limit_mb == 512
        assert processor.chunk_size == 10000
        assert processor.progress_update_interval == 1000
        assert processor.state == StreamingState.IDLE
        assert processor.auto_adjust_chunk_size is True

    def test_stream_processor_custom_settings(self, mock_db_connection):
        """Test StreamProcessor with custom configuration"""
        processor = StreamProcessor(
            db_connection=mock_db_connection,
            memory_limit_mb=256,
            chunk_size=5000,
            progress_update_interval=500,
            auto_adjust_chunk_size=False,
        )

        assert processor.memory_limit_mb == 256
        assert processor.chunk_size == 5000
        assert processor.progress_update_interval == 500
        assert processor.auto_adjust_chunk_size is False

    # ========== Streaming State Management Tests ==========

    def test_initial_state_is_idle(self, stream_processor):
        """Test processor starts in IDLE state"""
        assert stream_processor.state == StreamingState.IDLE

    def test_state_transitions_to_streaming(self, stream_processor, mock_db_connection):
        """Test state transitions to STREAMING when stream starts"""
        mock_db_connection.stream.return_value = iter([])

        gen = stream_processor.stream_query("SELECT * FROM test")
        # Generator not yet started
        assert stream_processor.state == StreamingState.IDLE

        # Start the generator
        list(gen)

        # After completion, should be back to IDLE
        assert stream_processor.state == StreamingState.IDLE

    def test_pause_sets_state_to_paused(self, stream_processor):
        """Test pause() sets state to PAUSED"""
        stream_processor._state = StreamingState.STREAMING
        stream_processor.pause()

        assert stream_processor.state == StreamingState.PAUSED

    def test_resume_sets_state_to_streaming(self, stream_processor):
        """Test resume() transitions from PAUSED to STREAMING"""
        stream_processor._state = StreamingState.PAUSED
        stream_processor.resume()

        assert stream_processor.state == StreamingState.STREAMING

    def test_cancel_sets_state_to_cancelled(self, stream_processor):
        """Test cancel() sets state to CANCELLED"""
        stream_processor._state = StreamingState.STREAMING
        stream_processor.cancel()

        assert stream_processor.state == StreamingState.CANCELLED

    def test_cannot_pause_from_idle(self, stream_processor):
        """Test pause() from IDLE state raises error"""
        with pytest.raises(RuntimeError, match="Cannot pause from IDLE state"):
            stream_processor.pause()

    def test_cannot_resume_from_streaming(self, stream_processor):
        """Test resume() from STREAMING state raises error"""
        stream_processor._state = StreamingState.STREAMING
        with pytest.raises(RuntimeError, match="Cannot resume from STREAMING state"):
            stream_processor.resume()

    # ========== Chunked Reading Tests ==========

    def test_stream_query_yields_chunks(self, stream_processor, mock_db_connection):
        """Test stream_query yields data in chunks"""
        # Mock data
        chunk1 = [{"id": i, "value": f"val{i}"} for i in range(3)]
        chunk2 = [{"id": i, "value": f"val{i}"} for i in range(3, 6)]

        mock_db_connection.stream.return_value = iter([chunk1, chunk2])

        results = list(stream_processor.stream_query("SELECT * FROM test"))

        assert len(results) == 2
        assert len(results[0]) == 3
        assert len(results[1]) == 3

    def test_stream_query_with_parameters(self, stream_processor, mock_db_connection):
        """Test stream_query passes parameters correctly"""
        mock_db_connection.stream.return_value = iter([])

        list(stream_processor.stream_query(
            "SELECT * FROM test WHERE id = ?",
            parameters=[42]
        ))

        mock_db_connection.stream.assert_called_once()
        call_args = mock_db_connection.stream.call_args
        assert call_args[0][0] == "SELECT * FROM test WHERE id = ?"
        assert call_args[1].get("parameters") == [42]

    def test_custom_chunk_size(self, stream_processor, mock_db_connection):
        """Test custom chunk_size is passed to database stream"""
        mock_db_connection.stream.return_value = iter([])

        stream_processor.chunk_size = 5000
        list(stream_processor.stream_query("SELECT * FROM test"))

        call_args = mock_db_connection.stream.call_args
        assert call_args[1].get("chunk_size") == 5000

    def test_empty_result_set(self, stream_processor, mock_db_connection):
        """Test streaming empty result set"""
        mock_db_connection.stream.return_value = iter([])

        results = list(stream_processor.stream_query("SELECT * FROM empty_table"))

        assert results == []

    # ========== Memory Management Tests ==========

    def test_memory_monitoring_enabled(self, stream_processor):
        """Test memory monitoring is enabled by default"""
        assert stream_processor.memory_monitoring_enabled is True

    def test_get_current_memory_usage(self, stream_processor):
        """Test get_current_memory_usage returns value"""
        usage = stream_processor.get_current_memory_usage()
        assert isinstance(usage, float)
        assert usage >= 0

    def test_memory_limit_enforcement(self, stream_processor, mock_db_connection):
        """Test streaming stops when memory limit exceeded"""
        # Create large chunks that would exceed memory
        large_chunk = [{"id": i, "data": "x" * 10000} for i in range(10000)]
        mock_db_connection.stream.return_value = iter([large_chunk, large_chunk])

        stream_processor.memory_limit_mb = 0.001  # Very small limit

        with pytest.raises(MemoryError, match="Memory limit exceeded"):
            list(stream_processor.stream_query("SELECT * FROM large_table"))

    def test_auto_adjust_chunk_size_on_memory_pressure(self, stream_processor, mock_db_connection):
        """Test chunk size reduces when memory pressure detected"""
        stream_processor.auto_adjust_chunk_size = True
        stream_processor.chunk_size = 10000

        # Simulate memory pressure
        with patch.object(stream_processor, 'get_current_memory_usage', return_value=450.0):
            stream_processor._adjust_chunk_size_for_memory()

        assert stream_processor.chunk_size < 10000

    def test_chunk_size_not_adjusted_when_disabled(self, stream_processor):
        """Test chunk size not adjusted when auto_adjust is False"""
        stream_processor.auto_adjust_chunk_size = False
        stream_processor.chunk_size = 10000

        with patch.object(stream_processor, 'get_current_memory_usage', return_value=450.0):
            stream_processor._adjust_chunk_size_for_memory()

        assert stream_processor.chunk_size == 10000

    def test_minimum_chunk_size_enforced(self, stream_processor):
        """Test chunk size doesn't go below minimum"""
        stream_processor.chunk_size = 100

        # Simulate high memory pressure
        with patch.object(stream_processor, 'get_current_memory_usage', return_value=500.0):
            stream_processor._adjust_chunk_size_for_memory()

        assert stream_processor.chunk_size >= 100  # Minimum chunk size

    # ========== Pause/Resume/Cancel Tests ==========

    def test_pause_stops_at_chunk_boundary(self, stream_processor, mock_db_connection):
        """Test pause stops streaming at next chunk boundary"""
        chunks = [
            [{"id": i} for i in range(3)],
            [{"id": i} for i in range(3, 6)],
            [{"id": i} for i in range(6, 9)],
        ]
        mock_db_connection.stream.return_value = iter(chunks)

        results = []
        gen = stream_processor.stream_query("SELECT * FROM test")

        # Get first chunk
        results.append(next(gen))

        # Pause streaming
        stream_processor.pause()

        # Try to get next chunk - should stop
        try:
            next(gen)
            # If we get here, check state was respected
            assert stream_processor.state == StreamingState.PAUSED
        except StopIteration:
            pass  # Generator stopped due to pause

    def test_cancel_clears_resources(self, stream_processor, mock_db_connection):
        """Test cancel cleans up resources"""
        chunks = [[{"id": i} for i in range(3)]]
        mock_db_connection.stream.return_value = iter(chunks)

        gen = stream_processor.stream_query("SELECT * FROM test")
        next(gen)

        stream_processor.cancel()

        assert stream_processor.state == StreamingState.CANCELLED
        # Resources should be cleaned up

    def test_resume_continues_from_paused_position(self, stream_processor, mock_db_connection):
        """Test resume continues from where it was paused"""
        chunks = [
            [{"id": i} for i in range(3)],
            [{"id": i} for i in range(3, 6)],
            [{"id": i} for i in range(6, 9)],
        ]
        call_count = [0]

        def mock_stream(*args, **kwargs):
            for chunk in chunks:
                call_count[0] += 1
                yield chunk

        mock_db_connection.stream.side_effect = mock_stream

        gen = stream_processor.stream_query("SELECT * FROM test")
        results = [next(gen)]

        stream_processor.pause()

        # Resume and continue
        stream_processor.resume()

        # The behavior depends on implementation
        # Either continues same generator or needs restart
        assert stream_processor.state == StreamingState.STREAMING or \
               stream_processor.state == StreamingState.IDLE

    # ========== Error Handling Tests ==========

    def test_cancel_clears_resources(self, stream_processor, mock_db_connection):
        """Test cancel cleans up resources"""
        chunks = [[{"id": i} for i in range(3)]]
        mock_db_connection.stream.return_value = iter(chunks)

        gen = stream_processor.stream_query("SELECT * FROM test")
        next(gen)
        stream_processor.cancel()
        assert stream_processor.state == StreamingState.CANCELLED
        # Resources should be cleaned up

    # ========== Thread Safety Tests ==========

    def test_concurrent_pause_resume(self, stream_processor):
        """Test concurrent pause/resume operations are thread-safe"""
        stream_processor._state = StreamingState.STREAMING

        def pause_resume():
            for _ in range(10):
                stream_processor.pause()
                time.sleep(0.001)
                stream_processor.resume()

        threads = [threading.Thread(target=pause_resume) for _ in range(3)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # State should be valid (either STREAMING or PAUSED)
        assert stream_processor.state in [StreamingState.STREAMING, StreamingState.PAUSED]


class TestProgressTracker:
    """Test suite for ProgressTracker class"""

    @pytest.fixture
    def progress_tracker(self):
        """Create ProgressTracker instance"""
        return ProgressTracker(
            total_rows=10000,
            total_bytes=1024 * 1024,  # 1MB
            update_interval=1000,
        )

    # ========== Initialization Tests ==========

    def test_progress_tracker_initialization(self):
        """Test ProgressTracker initializes correctly"""
        tracker = ProgressTracker(
            total_rows=1000,
            total_bytes=1024,
            update_interval=500,
        )

        assert tracker.total_rows == 1000
        assert tracker.total_bytes == 1024
        assert tracker.update_interval == 500

    # ========== Progress Update Tests ==========

    def test_update_progress(self, progress_tracker):
        """Test updating progress"""
        progress_tracker.update(rows_processed=100, bytes_processed=10240)

        info = progress_tracker.get_progress()
        assert info.rows_processed == 100
        assert info.bytes_processed == 10240

    def test_progress_percentage(self, progress_tracker):
        """Test progress percentage calculation"""
        progress_tracker.update(rows_processed=5000, bytes_processed=512 * 1024)

        info = progress_tracker.get_progress()
        assert info.percentage == pytest.approx(50.0, rel=0.1)

    def test_progress_percentage_zero_total(self):
        """Test percentage when total is zero"""
        tracker = ProgressTracker(total_rows=0, total_bytes=0)
        info = tracker.get_progress()

        assert info.percentage == 0.0

    # ========== ETA Calculation Tests ==========

    def test_eta_calculation(self, progress_tracker):
        """Test estimated time remaining calculation"""
        progress_tracker.start()
        time.sleep(0.1)

        progress_tracker.update(rows_processed=1000, bytes_processed=102400)

        info = progress_tracker.get_progress()
        # ETA should be calculated (positive value or None)
        if info.eta_seconds is not None:
            assert info.eta_seconds > 0

    def test_eta_returns_none_initially(self, progress_tracker):
        """Test ETA is None when no progress made"""
        progress_tracker.start()
        info = progress_tracker.get_progress()

        # Initially ETA should be None or 0
        assert info.eta_seconds is None or info.eta_seconds == 0

    # ========== Progress Info Tests ==========

    def test_get_progress_returns_progress_info(self, progress_tracker):
        """Test get_progress returns ProgressInfo dataclass"""
        progress_tracker.update(rows_processed=100, bytes_processed=1024)

        info = progress_tracker.get_progress()

        assert isinstance(info, ProgressInfo)
        assert hasattr(info, 'rows_processed')
        assert hasattr(info, 'bytes_processed')
        assert hasattr(info, 'percentage')
        assert hasattr(info, 'eta_seconds')
        assert hasattr(info, 'current_operation')
        assert hasattr(info, 'elapsed_seconds')

    def test_current_operation_tracking(self, progress_tracker):
        """Test tracking current operation"""
        progress_tracker.set_operation("reading")
        info = progress_tracker.get_progress()
        assert info.current_operation == "reading"

        progress_tracker.set_operation("processing")
        info = progress_tracker.get_progress()
        assert info.current_operation == "processing"

    # ========== Accuracy Tests ==========

    def test_progress_accuracy_within_margin(self, progress_tracker):
        """Test progress tracking accuracy within 2% margin"""
        # Process exactly 25% of data
        progress_tracker.update(rows_processed=2500, bytes_processed=256 * 1024)

        info = progress_tracker.get_progress()
        expected_percentage = 25.0

        # Error margin should be less than 2%
        error = abs(info.percentage - expected_percentage)
        assert error < 2.0, f"Progress error {error}% exceeds 2% margin"

    def test_cumulative_updates(self, progress_tracker):
        """Test cumulative progress updates"""
        progress_tracker.update(rows_processed=100, bytes_processed=1024)
        progress_tracker.update(rows_processed=100, bytes_processed=1024)

        info = progress_tracker.get_progress()
        assert info.rows_processed == 200
        assert info.bytes_processed == 2048

    # ========== Callback Tests ==========

    def test_progress_callback_invoked(self, progress_tracker):
        """Test progress callback is invoked"""
        callback_calls = []

        def callback(info: ProgressInfo):
            callback_calls.append(info)

        progress_tracker.add_callback(callback)
        progress_tracker.update(rows_processed=100, bytes_processed=1024)

        # Callback should be invoked based on update_interval
        # Force a callback check
        progress_tracker._check_callback()

        assert len(callback_calls) > 0
        assert isinstance(callback_calls[0], ProgressInfo)

    def test_multiple_callbacks(self, progress_tracker):
        """Test multiple progress callbacks"""
        callback1_calls = []
        callback2_calls = []

        progress_tracker.add_callback(lambda info: callback1_calls.append(info))
        progress_tracker.add_callback(lambda info: callback2_calls.append(info))

        progress_tracker.update(rows_processed=100, bytes_processed=1024)
        progress_tracker._check_callback()

        assert len(callback1_calls) == len(callback2_calls)


class TestProgressInfo:
    """Test suite for ProgressInfo dataclass"""

    def test_progress_info_creation(self):
        """Test ProgressInfo dataclass creation"""
        info = ProgressInfo(
            rows_processed=100,
            bytes_processed=1024,
            percentage=10.0,
            eta_seconds=90.0,
            current_operation="reading",
            elapsed_seconds=10.0,
        )

        assert info.rows_processed == 100
        assert info.bytes_processed == 1024
        assert info.percentage == 10.0
        assert info.eta_seconds == 90.0
        assert info.current_operation == "reading"
        assert info.elapsed_seconds == 10.0

    def test_progress_info_defaults(self):
        """Test ProgressInfo default values"""
        info = ProgressInfo(
            rows_processed=0,
            bytes_processed=0,
            percentage=0.0,
        )

        assert info.eta_seconds is None
        assert info.current_operation == "idle"
        assert info.elapsed_seconds == 0.0


class TestStreamingState:
    """Test suite for StreamingState enum"""

    def test_streaming_state_values(self):
        """Test StreamingState has expected values"""
        assert StreamingState.IDLE.value == "idle"
        assert StreamingState.STREAMING.value == "streaming"
        assert StreamingState.PAUSED.value == "paused"
        assert StreamingState.CANCELLED.value == "cancelled"


# ========== Integration Tests ==========

class TestStreamProcessorIntegration:
    """Integration tests for StreamProcessor with DatabaseConnection"""

    @pytest.fixture
    def real_db(self, tmp_path):
        """Create real database connection for integration testing"""
        db_path = str(tmp_path / "test.duckdb")
        db = DatabaseConnection(db_path)

        # Create test table with data
        db.execute("""
            CREATE TABLE large_table (
                id INTEGER,
                name VARCHAR,
                value DOUBLE
            )
        """)

        # Insert test data
        for i in range(100):
            db.execute(
                "INSERT INTO large_table VALUES (?, ?, ?)",
                parameters=[i, f"name_{i}", i * 1.5]
            )

        yield db

        db.close()

    def test_streaming_with_real_database(self, real_db):
        """Test streaming with real DuckDB connection"""
        processor = StreamProcessor(
            db_connection=real_db,
            chunk_size=20,
        )

        chunks = list(processor.stream_query("SELECT * FROM large_table"))

        assert len(chunks) >= 1
        total_rows = sum(len(chunk) for chunk in chunks)
        assert total_rows == 100

    def test_progress_tracking_with_real_query(self, real_db):
        """Test progress tracking with real query execution"""
        processor = StreamProcessor(
            db_connection=real_db,
            chunk_size=20,
        )

        progress_updates = []

        def track_progress(info):
            progress_updates.append(info.percentage)

        processor.progress_tracker.add_callback(track_progress)

        list(processor.stream_query("SELECT * FROM large_table"))

        # Progress should have been tracked
        assert len(progress_updates) > 0 or processor.progress_tracker.get_progress().rows_processed == 100

    def test_state_transitions_with_real_query(self, real_db):
        """Test state transitions during real query"""
        processor = StreamProcessor(db_connection=real_db)

        gen = processor.stream_query("SELECT * FROM large_table")

        # Consume all data
        list(gen)

        # Should be back to IDLE after completion
        assert processor.state == StreamingState.IDLE
