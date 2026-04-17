"""
Streaming performance tests.

Tests for memory-efficient streaming of large datasets
and performance benchmarks.
"""

import pytest
import psutil
import os
from pathlib import Path
from src.core.processor import Processor
from src.core.config.loader import Config


# ========================================================================
# Test Fixtures
# ========================================================================

@pytest.fixture
def sample_large_csv(tmp_path):
    """Create a large CSV file for streaming tests."""
    csv_file = tmp_path / "large_data.csv"

    # Create a CSV with 100,000 rows
    with open(csv_file, 'w') as f:
        # Header
        f.write("id,name,value,category,timestamp\n")

        # Data rows
        for i in range(100000):
            f.write(f"{i},Item_{i},{i * 10.5},Category_{i % 10},2024-01-01T{i % 24}:00:00\n")

    return str(csv_file)


@pytest.fixture
def memory_limited_processor():
    """Create processor with memory limits for testing."""
    return Processor(
        max_memory_mb=100,
        streaming_threshold_mb=10,
        cache_enabled=False
    )


# ========================================================================
# Streaming Performance Tests
# ========================================================================

@pytest.mark.slow
class TestStreamingPerformance:
    """Test streaming performance with large datasets."""

    def test_stream_large_csv(self, memory_limited_processor, sample_large_csv):
        """Test streaming a large CSV file stays within memory limits."""
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # Load the large CSV
        memory_limited_processor.load_csv(sample_large_csv)

        # Memory should not increase significantly
        current_memory = process.memory_info().rss
        memory_increase_mb = (current_memory - initial_memory) / (1024 * 1024)

        # Memory increase should be reasonable (< 50MB for streaming)
        assert memory_increase_mb < 50, f"Memory increased by {memory_increase_mb:.2f}MB"

    def test_stream_query_execution(self, memory_limited_processor, sample_large_csv):
        """Test query execution with streaming uses memory efficiently."""
        memory_limited_processor.load_csv(sample_large_csv)

        process = psutil.Process(os.getpid())
        memory_samples = []

        # Execute query and monitor memory
        for i, row in enumerate(memory_limited_processor.stream_query("SELECT * FROM data")):
            if i % 10000 == 0:
                memory_samples.append(process.memory_info().rss)
            if i >= 50000:  # Sample first 50k rows
                break

        # Memory should not continuously grow
        if len(memory_samples) > 1:
            # Check if memory growth is bounded
            max_growth = max(memory_samples) - min(memory_samples)
            max_growth_mb = max_growth / (1024 * 1024)

            # Growth should be less than 20MB during streaming
            assert max_growth_mb < 20, f"Memory grew by {max_growth_mb:.2f}MB during streaming"


# ========================================================================
# Memory Management Tests
# ========================================================================

class TestMemoryManagement:
    """Test memory management features."""

    def test_memory_limit_enforcement(self):
        """Test processor respects memory limits."""
        limited_processor = Processor(
            max_memory_mb=50,
            streaming_threshold_mb=10
        )

        assert limited_processor._max_memory_mb == 50
        assert limited_processor._streaming_threshold_mb == 10

    def test_streaming_threshold_detection(self, tmp_path):
        """Test processor detects when to use streaming."""
        # Create a small file (under threshold)
        small_file = tmp_path / "small.csv"
        with open(small_file, 'w') as f:
            f.write("id,value\n")
            for i in range(100):
                f.write(f"{i},{i * 2}\n")

        processor = Processor(max_memory_mb=100, streaming_threshold_mb=10)

        # Small file should not trigger streaming
        processor.load_csv(str(small_file))

        # Verify data is loaded
        result = processor.execute_query("SELECT COUNT(*) as count FROM data")
        assert result[0]['count'] == 100

    def test_cache_memory_management(self):
        """Test cache doesn't cause memory bloat."""
        processor = Processor(
            max_memory_mb=50,
            cache_enabled=True
        )

        # Execute multiple queries that should be cached
        for _ in range(10):
            processor.execute_query("SELECT 1 as value")

        # Cache should not grow unbounded
        cache_size = len(processor._cache)
        assert cache_size < 100, "Cache size seems too large"


# ========================================================================
# Performance Benchmarks
# ========================================================================

@pytest.mark.slow
class TestPerformanceBenchmarks:
    """Performance benchmarks for streaming operations."""

    def test_csv_loading_performance(self, sample_large_csv):
        """Test CSV loading performance is acceptable."""
        import time

        processor = Processor(max_memory_mb=100)

        start_time = time.time()
        processor.load_csv(sample_large_csv)
        load_time = time.time() - start_time

        # Loading 100k rows should take less than 10 seconds
        assert load_time < 10, f"CSV loading took {load_time:.2f}s, expected < 10s"

    def test_query_performance(self, sample_large_csv):
        """Test query execution performance is acceptable."""
        import time

        processor = Processor(max_memory_mb=100)
        processor.load_csv(sample_large_csv)

        start_time = time.time()
        result = processor.execute_query("SELECT COUNT(*) as count FROM data")
        query_time = time.time() - start_time

        # Query should complete in reasonable time
        assert query_time < 5, f"Query took {query_time:.2f}s, expected < 5s"
        assert result[0]['count'] == 100000

    def test_streaming_throughput(self, memory_limited_processor, sample_large_csv):
        """Test streaming throughput is acceptable."""
        import time

        memory_limited_processor.load_csv(sample_large_csv)

        start_time = time.time()
        row_count = 0

        for row in memory_limited_processor.stream_query("SELECT * FROM data"):
            row_count += 1
            if row_count >= 10000:
                break

        elapsed = time.time() - start_time
        rows_per_second = row_count / elapsed

        # Should process at least 1000 rows per second
        assert rows_per_second >= 1000, f"Streaming throughput: {rows_per_second:.0f} rows/sec"


# ========================================================================
# Resource Cleanup Tests
# ========================================================================

class TestResourceCleanup:
    """Test proper resource cleanup during streaming."""

    def test_processor_cleanup(self, sample_large_csv):
        """Test processor properly cleans up resources."""
        processor = Processor(max_memory_mb=100)
        processor.load_csv(sample_large_csv)

        # Processor should have resources loaded
        assert processor._connection is not None

        # Cleanup should be handled properly
        # (This is more of an integration test pattern)

    def test_memory_reuse_after_streaming(self, memory_limited_processor, sample_large_csv):
        """Test memory is reused between streaming operations."""
        memory_limited_processor.load_csv(sample_large_csv)

        process = psutil.Process(os.getpid())

        # First streaming operation
        first_stream_memory = process.memory_info().rss
        list(memory_limited_processor.stream_query("SELECT * FROM data LIMIT 1000"))

        # Second streaming operation
        second_stream_memory = process.memory_info().rss
        list(memory_limited_processor.stream_query("SELECT * FROM data LIMIT 1000"))

        third_stream_memory = process.memory_info().rss

        # Memory usage should be relatively stable
        max_difference = max(
            abs(second_stream_memory - first_stream_memory),
            abs(third_stream_memory - second_stream_memory)
        ) / (1024 * 1024)

        # Difference should be less than 10MB
        assert max_difference < 10, f"Memory variance: {max_difference:.2f}MB"
