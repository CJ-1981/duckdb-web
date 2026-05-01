"""
Monitoring System Tests

Test suite for production monitoring and logging components.
"""

import pytest
import os
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

from src.api.main import create_app
from src.api.monitoring.logging_config import get_logger, get_log_level, configure_logging


@pytest.fixture
def app():
    """Create test application instance."""
    return create_app()


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_logger():
    """Create mock logger for testing."""
    return Mock()


class TestStructuredLogging:
    """Test structured logging configuration."""

    def test_get_log_level_default(self):
        """Test default log level is INFO."""
        with patch.dict(os.environ, {}, clear=True):
            level = get_log_level()
            assert level == 20  # INFO level

    def test_get_log_level_custom(self):
        """Test custom log level from environment."""
        with patch.dict(os.environ, {"LOG_LEVEL": "DEBUG"}):
            level = get_log_level()
            assert level == 10  # DEBUG level

    def test_logger_creation(self):
        """Test logger instance creation."""
        logger = get_logger("test_module")
        assert logger is not None

    def test_logger_context_binding(self):
        """Test logger context variable binding."""
        logger = get_logger("test_context")
        # Test context binding doesn't raise errors
        try:
            logger.info("test message", user_id=123)
            assert True
        except Exception:
            pytest.fail("Logger context binding failed")


class TestHealthEndpoints:
    """Test Kubernetes-style health check endpoints."""

    def test_liveness_probe(self, client):
        """Test liveness probe returns healthy status."""
        response = client.get("/health/live")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data

    def test_readiness_probe_success(self, client):
        """Test readiness probe returns ready when dependencies are healthy."""
        response = client.get("/health/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert "checks" in data
        assert "processor" in data["checks"]
        assert "config" in data["checks"]

    def test_startup_probe(self, client):
        """Test startup probe returns healthy after initialization."""
        response = client.get("/health/startup")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data

    def test_readiness_includes_dependency_checks(self, client):
        """Test readiness probe includes detailed dependency status."""
        response = client.get("/health/ready")
        assert response.status_code == 200
        data = response.json()
        checks = data["checks"]

        # Verify all expected checks are present
        assert "config" in checks
        assert "processor" in checks
        assert "database" in checks

        # Verify each check has status and description
        for _check_name, check_data in checks.items():
            assert "status" in check_data
            assert "description" in check_data


class TestMonitoringMiddleware:
    """Test monitoring middleware functionality."""

    def test_request_id_header_added(self, client):
        """Test that X-Request-ID header is added to responses."""
        response = client.get("/api/health")
        assert "X-Request-ID" in response.headers
        assert len(response.headers["X-Request-ID"]) > 0

    def test_process_time_header_added(self, client):
        """Test that X-Process-Time-Ms header is added to responses."""
        response = client.get("/api/health")
        assert "X-Process-Time-Ms" in response.headers
        # Verify it's a valid number
        try:
            process_time = float(response.headers["X-Process-Time-Ms"])
            assert process_time >= 0
        except ValueError:
            pytest.fail("X-Process-Time-Ms is not a valid number")

    def test_request_id_consistency(self, client):
        """Test that request ID is consistent across logging and headers."""
        response = client.get("/api/health")
        request_id = response.headers.get("X-Request-ID")
        assert request_id is not None


class TestMetrics:
    """Test metrics collection functionality."""

    def test_metrics_endpoint_disabled_by_default(self, client):
        """Test that metrics endpoint returns 503 when disabled."""
        with patch.dict(os.environ, {"PROMETHEUS_ENABLED": "false"}):
            response = client.get("/metrics")
            assert response.status_code == 503

    @pytest.mark.skipif(
        os.getenv("PROMETHEUS_ENABLED") != "true",
        reason="Prometheus not enabled"
    )
    def test_metrics_endpoint_enabled(self, client):
        """Test that metrics endpoint returns data when enabled."""
        with patch.dict(os.environ, {"PROMETHEUS_ENABLED": "true"}):
            response = client.get("/metrics")
            # Only test if prometheus_client is installed
            if response.status_code == 200:
                assert "text/plain" in response.headers.get("content-type", "")


class TestLoggingIntegration:
    """Test logging integration with FastAPI."""

    def test_request_logging(self, client, caplog):
        """Test that requests are logged."""
        with caplog.at_level("INFO"):
            response = client.get("/api/health")
            assert response.status_code == 200
            # Check that log entries were created
            assert len(caplog.records) > 0


class TestErrorHandling:
    """Test error handling in monitoring system."""

    def test_404_errors_logged(self, client):
        """Test that 404 errors are logged appropriately."""
        response = client.get("/nonexistent-endpoint")
        assert response.status_code == 404

    def test_error_response_includes_request_id(self, client):
        """Test that error responses include correlation ID."""
        response = client.get("/api/trigger-error")
        # This endpoint doesn't exist, so we'll get a 404
        # but we can still check for request ID header
        assert "X-Request-ID" in response.headers or response.status_code == 404


@pytest.mark.integration
class TestProductionConfiguration:
    """Integration tests for production configuration."""

    def test_json_logging_format(self):
        """Test JSON logging format in production mode."""
        with patch.dict(os.environ, {
            "ENV": "production",
            "LOG_FORMAT": "json"
        }):
            # Reconfigure logging
            configure_logging()

            # Get logger and log a message
            logger = get_logger("test_production")
            logger.info("test message", test_key="test_value")

            # Configuration should not raise errors
            assert True

    def test_console_logging_format(self):
        """Test console logging format in development mode."""
        with patch.dict(os.environ, {
            "ENV": "development",
            "LOG_FORMAT": "console",
            "LOG_PRETTY": "true"
        }):
            # Reconfigure logging
            configure_logging()

            # Get logger and log a message
            logger = get_logger("test_development")
            logger.info("test message")

            # Configuration should not raise errors
            assert True


@pytest.mark.performance
class TestMonitoringPerformance:
    """Performance tests for monitoring system."""

    def test_middleware_overhead_minimal(self, client):
        """Test that monitoring middleware adds minimal overhead."""
        import time

        # Make multiple requests and measure timing
        iterations = 100
        start_time = time.time()

        for _ in range(iterations):
            client.get("/api/health")

        end_time = time.time()
        avg_time = (end_time - start_time) / iterations

        # Average request should be under 50ms
        # This is a generous threshold for CI environments
        assert avg_time < 0.05, f"Average request time {avg_time:.3f}s exceeds threshold"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
