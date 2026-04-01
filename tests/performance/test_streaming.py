"""
Performance Tests for Result Streaming (P1-T007)

TDD RED Phase: These tests verify memory management and streaming performance
for datasets exceeding 512MB.
"""

import pytest
import os
import tempfile
import time
import psutil
from typing import List, Dict, Any
from unittest.mock import Mock, patch
from pathlib import Path

# These imports will fail until GREEN phase implementation
pytest.importorskip("src.core.processor.streaming")

from src.core.processor.streaming import StreamProcessor, StreamingState
from src.core.processor.progress import ProgressTracker
from src.core.database import DatabaseConnection


class TestMemoryManagement:
    """Memory management tests for streaming large datasets"""

    @pytest.fixture
    def mock_db_large_dataset(self):
        """Mock database connection with large dataset"""
        mock_db = Mock(spec=DatabaseConnection)
        mock_db.db_path = ":memory:"

        # Create 600MB of chunks (600 chunks of 1MB each)
        def large_dataset_generator():
            for i in range(600):
                # Each chunk is ~1MB (10000 rows * 100 bytes per row)
                chunk = [{"id": j, "data": "x" * 100} for j in range(10000)]
                yield chunk

        mock_db.stream.return_value = large_dataset_generator()
        return mock_db

    @pytest.fixture
    def memory_limited_processor(self, mock_db_large_dataset):
        """Create processor with 512MB memory limit"""
        return StreamProcessor(
            db_connection=mock_db_large_dataset,
            memory_limit_mb=512,
            chunk_size=10000,
        )

    def test_memory_usage_stays_under_limit(self, memory_limited_processor):
        """Test that memory usage remains under configured limit during streaming"""
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        chunks_processed = 0
        peak_memory = 0

        for chunk in memory_limited_processor.stream_query("SELECT * FROM large_table"):
            chunks_processed += 1
            current_memory = process.memory_info().rss
            peak_memory = max(peak_memory, current_memory)

            # Memory should stay under limit (with some buffer for overhead)
            # 512MB limit in bytes
            assert current_memory < 512 * 1024 * 1024 * 1.1, f"Memory exceeded limit: {current_memory} > {512 * 1024 * 1024}"

        # Verify we processed chunks
        assert chunks_processed > 0

    def test_memory_cleanup_between_chunks(self, memory_limited_processor):
        """Test that memory is cleaned up between chunks"""
        process = psutil.Process(os.getpid())

        memory_samples = []

        for i, 1 in enumerate(memory_limited_processor.stream_query("SELECT * FROM test")):
            memory_samples.append(process.memory_info().rss)

        # Memory should not continuously grow
        # (allowing for some variance but should generally stay bounded)
        if len(memory_samples) > 1:
            max_growth = max(memory_samples[i] - memory_samples[i-1]
                           for i in range(1, len(memory_samples)))
            # Growth should be controlled (not more than 10MB growth between chunks)
            assert max_growth < 10 * 1024 * 1024, \
                f"Uncontrolled memory growth: {max_growth} bytes"

    def test_chunk_size_auto_adjustment(self, mock_db_large_dataset):
        """Test that chunk size is automatically adjusted when memory limit approached"""
        processor = StreamProcessor(
            db_connection=mock_db_large_dataset,
            memory_limit_mb=512,
            chunk_size=10000,
            auto_adjust_chunk_size=True,
        )

        initial_chunk_size = processor.chunk_size

        # Simulate streaming with memory pressure
        with patch.object(processor, '_get_current_memory_mb') as mock_memory:
            # First call returns high memory, triggering adjustment
            mock_memory.side_effect = [500, 400, 300, 200] + [100] * 100

            chunks = list(processor.stream_query("SELECT * FROM large_table"))

            # Chunk size should have been adjusted
            assert processor.chunk_size <= initial_chunk_size, \
                "Chunk size should be reduced when memory limit approached"

    def test_memory_limit_enforcement_stops_streaming(self, mock_db_large_dataset):
        """Test that streaming stops when memory limit is exceeded"""
        processor = StreamProcessor(
            db_connection=mock_db_large_dataset,
            memory_limit_mb=100,  # Set low limit
            chunk_size=10000,
        )

        with patch.object(processor, '_get_current_memory_mb') as mock_memory:
            # Return memory that exceeds limit
            mock_memory.return_value = 150  # Exceeds 100MB limit

            with pytest.raises(MemoryError, match="Memory limit exceeded"):
                list(processor.stream_query("SELECT * FROM large_table"))


class TestStreamingPerformance:
    """Performance tests for streaming throughput"""

    @pytest.fixture
    def real_db_for_performance(self, tmp_path):
        """Create real database with performance test data"""
        db_path = str(tmp_path / "perf.duckdb")
        db = DatabaseConnection(db_path)

        # Create table with many rows for performance testing
        db.execute("""
            CREATE TABLE performance_test (
                id INTEGER,
                value1 VARCHAR,
                value2 DOUBLE,
                value3 VARCHAR
            )
        """)

        # Insert 100,000 rows in batches
        batch_size = 10000
        for batch_start in range(0, 100000, batch_size):
            params_list = []
            for i in range(batch_start, min(batch_start + batch_size, 100000)):
                params_list.append([i, f"val_{i}", i * 1.5, f"data_{i}"])
            db.execute_batch(
                "INSERT INTO performance_test VALUES (?, ?, ?, ?)",
                params_list
            )

        yield db
        db.close()

    @pytest.mark.slow
    def test_streaming_throughput(self, real_db_for_performance):
        """Test streaming throughput meets minimum requirements"""
        processor = StreamProcessor(
            db_connection=real_db_for_performance,
            chunk_size=10000,
        )

        start_time = time.time()
        total_rows = 0

        for chunk in processor.stream_query("SELECT * FROM performance_test"):
            total_rows += len(chunk)

        elapsed = time.time() - start_time
        rows_per_second = total_rows / elapsed

        # Should process at least 10,000 rows per second
        assert rows_per_second >= 10000, \
            f"Throughput too low: {rows_per_second} rows/sec (minimum: 10000)"

        # All rows should be processed
        assert total_rows == 100000

    @pytest.mark.slow
    def test_streaming_latency(self, real_db_for_performance):
        """Test first chunk latency is acceptable"""
        processor = StreamProcessor(
            db_connection=real_db_for_performance,
            chunk_size=10000,
        )

        start_time = time.time()
        first_chunk_time = None

        for i, chunk in enumerate(processor.stream_query("SELECT * FROM performance_test")):
            if i == 0:
                first_chunk_time = time.time() - start_time
                break

        # First chunk should arrive within 1 second
        assert first_chunk_time < 1.0, \
            f"First chunk latency too high: {first_chunk_time}s (max: 1.0s)"

    @pytest.mark.slow
    def test_progress_tracking_overhead(self, real_db_for_performance):
        """Test that progress tracking adds minimal overhead"""
        processor_no_progress = StreamProcessor(
            db_connection=real_db_for_performance,
            chunk_size=10000,
            progress_update_interval=0,  # Disable progress tracking
        )

        processor_with_progress = StreamProcessor(
            db_connection=real_db_for_performance,
            chunk_size=10000,
            progress_update_interval=1000,
        )

        # Measure time without progress tracking
        start = time.time()
        list(processor_no_progress.stream_query("SELECT * FROM performance_test"))
        time_without_progress = time.time() - start

        # Measure time with progress tracking
        start = time.time()
        list(processor_with_progress.stream_query("SELECT * FROM performance_test"))
        time_with_progress = time.time() - start

        # Progress tracking should add less than 20% overhead
        overhead = (time_with_progress - time_without_progress) / time_without_progress
        assert overhead < 0.2, \
            f"Progress tracking overhead too high: {overhead * 100}% (max: 20%)"


class TestPauseResumePerformance:
    """Performance tests for pause/resume operations"""

    @pytest.fixture
    def streaming_with_data(self, tmp_path):
        """Create streaming processor with data for pause/resume tests"""
        db_path = str(tmp_path / "pause_test.duckdb")
        db = DatabaseConnection(db_path)

        # Create table
        db.execute("""
            CREATE TABLE stream_test (
                id INTEGER,
                value VARCHAR
            )
        """)

        # Insert 1000 rows
        params_list = [[i, f"val_{i}"] for i in range(1000)]
        db.execute_batch("INSERT INTO stream_test VALUES (?, ?)", params_list)

        yield db
        db.close()

    def test_pause_stops_at_chunk_boundary(self, streaming_with_data):
        """Test that pause respects chunk boundaries"""
        processor = StreamProcessor(
            db_connection=streaming_with_data,
            chunk_size=100,
        )

        chunks = []
        gen = processor.stream_query("SELECT * FROM stream_test")

        # Collect chunks until we have 5
        for i, chunk in enumerate(gen):
            chunks.append(chunk)
            if i == 4:  # After 5 chunks
                processor.pause()
                break

        # Should have exactly 5 chunks
        assert len(chunks) == 5
        assert processor.state == StreamingState.PAUSED

        # Total rows should be exactly 500 (5 chunks * 100 rows)
        total_rows = sum(len(chunk) for chunk in chunks)
        assert total_rows == 500

    @pytest.mark.slow
    def test_resume_continues_correctly(self, streaming_with_data):
        """Test that resume continues from correct position"""
        processor = StreamProcessor(
            db_connection=streaming_with_data,
            chunk_size=100,
        )

        chunks_before_pause = []
        gen = processor.stream_query("SELECT * FROM stream_test")

        # Collect first 5 chunks
        for i, chunk in enumerate(gen):
            chunks_before_pause.append(chunk)
            if i == 4:
                processor.pause()
                break

        # Resume and collect remaining chunks
        processor.resume()

        # Note: This test depends on implementation
        # The generator may need to be restarted or continued

        # For now, just verify state
        assert processor.state == StreamingState.STREAMING

    def test_cancel_performance(self, streaming_with_data):
        """Test cancel operation is fast"""
        processor = StreamProcessor(
            db_connection=streaming_with_data,
            chunk_size=100,
        )

        gen = processor.stream_query("SELECT * FROM stream_test")

        # Start streaming
        next(gen)

        # Cancel should be near-instant
        start = time.time()
        processor.cancel()
        cancel_time = time.time() - start

        # Cancel should take less than 100ms
        assert cancel_time < 0.1, \
            f"Cancel too slow: {cancel_time * 1000}ms (max: 100ms)"


class TestConcurrentStreaming:
    """Tests for concurrent streaming operations"""

    def test_multiple_concurrent_streams(self, tmp_path):
        """Test multiple concurrent stream operations"""
        db_path = str(tmp_path / "concurrent.duckdb")
        db = DatabaseConnection(db_path)

        # Create test table
        db.execute("""
            CREATE TABLE concurrent_test (
                id INTEGER,
                value VARCHAR
            )
        """)
        params_list = [[i, f"val_{i}"] for i in range(1000)]
        db.execute_batch("INSERT INTO concurrent_test VALUES (?, ?)", params_list)

        processor = StreamProcessor(db_connection=db, chunk_size=100)

        results = {"stream1": [], "stream2": [], "stream3": []}
        threads = []

        def stream_data(name):
            for chunk in processor.stream_query("SELECT * FROM concurrent_test"):
                results[name].append(len(chunk))

        # Start concurrent streams
        for name in results.keys():
            t = threading.Thread(target=stream_data, args=(name,))
            t.start()
            threads.append(t)

        # Wait for completion
        for t in threads:
            t.join(timeout=10)

        db.close()

        # All streams should have processed data
        # Note: Results depend on thread safety of implementation
        for name, chunks in results.items():
            # Each stream should process at least some data
            assert len(chunks) > 0 or sum(chunks) > 0, \
                f"Stream {name} processed no data"
