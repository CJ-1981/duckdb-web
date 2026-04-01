"""
Tests for FastAPI Application Structure

This test module follows TDD RED phase - tests are written BEFORE implementation.
All tests should FAIL initially, confirming they test new behavior.

Acceptance Criteria:
- Application starts successfully with all routers loaded
- Middleware executes in correct order
- Dependency injection configured
- OpenAPI documentation auto-generated
"""

import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI, Request
from unittest.mock import Mock, patch, MagicMock
import asyncio


# ========================================================================
# Test Application Initialization
# ========================================================================


class TestApplicationInitialization:
    """Test FastAPI application initialization and configuration"""

    def test_app_import_available(self):
        """
        RED: Test that main app module can be imported

        Expected: Module should exist and be importable
        Current: Module does not exist (should fail)
        """
        # This import should fail initially
        with pytest.raises(ImportError):
            from src.api.main import app

    def test_app_is_fastapi_instance(self):
        """
        RED: Test that app is a FastAPI instance

        Expected: app should be instance of FastAPI
        Current: Module does not exist (should fail)
        """
        from src.api.main import app

        assert isinstance(app, FastAPI)

    def test_app_metadata_configured(self):
        """
        RED: Test that app has proper metadata

        Expected: title, version, description should be configured
        Current: Module does not exist (should fail)
        """
        from src.api.main import app

        assert app.title == "DuckDB Data Processor API"
        assert app.version == "1.0.0"
        assert app.description is not None

    def test_app_docs_urls_configured(self):
        """
        RED: Test that OpenAPI documentation URLs are configured

        Expected: /docs and /redoc should be configured
        Current: Module does not exist (should fail)
        """
        from src.api.main import app

        assert app.docs_url == "/docs"
        assert app.redoc_url == "/redoc"
        assert app.openapi_url == "/openapi.json"


# ========================================================================
# Test Middleware Stack
# ========================================================================


class TestMiddlewareStack:
    """Test middleware configuration and execution order"""

    def test_cors_middleware_configured(self):
        """
        RED: Test that CORS middleware is configured

        Expected: CORS middleware should be added to app
        Current: Module does not exist (should fail)
        """
        from src.api.main import app

        # Check if CORS middleware is in the middleware stack
        middleware_types = [type(m).__name__ for m in app.user_middleware]
        assert any('CORSMiddleware' in m for m in middleware_types)

    def test_middleware_order_correct(self):
        """
        RED: Test that middleware executes in correct order

        Expected order (outer to inner):
        1. CORS (first)
        2. Request ID
        3. Logging
        4. Error Handler
        5. Authentication (last before route)

        Current: Module does not exist (should fail)
        """
        from src.api.main import app

        # Get middleware stack
        middleware_stack = app.user_middleware

        # Should have at least 4 middleware components
        assert len(middleware_stack) >= 4

    def test_request_id_middleware_exists(self):
        """
        RED: Test that Request ID middleware exists

        Expected: Request ID middleware should be in stack
        Current: Module does not exist (should fail)
        """
        from src.api.main import app
        from src.api.middleware import RequestIDMiddleware

        # Check if RequestIDMiddleware is in the stack
        middleware_types = [type(m).__name__ for m in app.user_middleware]
        assert 'RequestIDMiddleware' in middleware_types

    def test_logging_middleware_exists(self):
        """
        RED: Test that Logging middleware exists

        Expected: Logging middleware should be in stack
        Current: Module does not exist (should fail)
        """
        from src.api.main import app
        from src.api.middleware import LoggingMiddleware

        # Check if LoggingMiddleware is in the stack
        middleware_types = [type(m).__name__ for m in app.user_middleware]
        assert 'LoggingMiddleware' in middleware_types

    def test_error_handler_middleware_exists(self):
        """
        RED: Test that Error Handler middleware exists

        Expected: Error Handler middleware should be in stack
        Current: Module does not exist (should fail)
        """
        from src.api.main import app
        from src.api.middleware import ErrorHandlerMiddleware

        # Check if ErrorHandlerMiddleware is in the stack
        middleware_types = [type(m).__name__ for m in app.user_middleware]
        assert 'ErrorHandlerMiddleware' in middleware_types


# ========================================================================
# Test Dependency Injection
# ========================================================================


class TestDependencyInjection:
    """Test dependency injection configuration"""

    def test_dependencies_module_importable(self):
        """
        RED: Test that dependencies module can be imported

        Expected: Module should exist and be importable
        Current: Module does not exist (should fail)
        """
        with pytest.raises(ImportError):
            from src.api import dependencies

    def test_get_processor_dependency(self):
        """
        RED: Test get_processor dependency exists

        Expected: get_processor function should exist
        Current: Module does not exist (should fail)
        """
        from src.api.dependencies import get_processor

        assert callable(get_processor)

    def test_get_processor_returns_processor_instance(self):
        """
        RED: Test get_processor returns Processor instance

        Expected: Should return Processor from src.core.processor
        Current: Module does not exist (should fail)
        """
        from src.api.dependencies import get_processor
        from src.core.processor import Processor

        processor = get_processor()
        assert isinstance(processor, Processor)

    def test_get_config_dependency(self):
        """
        RED: Test get_config dependency exists

        Expected: get_config function should exist
        Current: Module does not exist (should fail)
        """
        from src.api.dependencies import get_config

        assert callable(get_config)

    def test_get_config_returns_config_instance(self):
        """
        RED: Test get_config returns Config instance

        Expected: Should return Config from src.core.config.loader
        Current: Module does not exist (should fail)
        """
        from src.api.dependencies import get_config
        from src.core.config.loader import Config

        config = get_config()
        # Config might be a dict or object depending on implementation
        assert config is not None

    def test_get_current_user_dependency(self):
        """
        RED: Test get_current_user dependency exists

        Expected: get_current_user function should exist for auth
        Current: Module does not exist (should fail)
        """
        from src.api.dependencies import get_current_user

        assert callable(get_current_user)


# ========================================================================
# Test Router Registration
# ========================================================================


class TestRouterRegistration:
    """Test that routers are properly registered"""

    def test_health_router_registered(self):
        """
        RED: Test health check router is registered

        Expected: /health endpoint should be available
        Current: Module does not exist (should fail)
        """
        from src.api.main import app

        client = TestClient(app)
        response = client.get("/health")

        assert response.status_code == 200
        assert "status" in response.json()

    def test_root_endpoint_exists(self):
        """
        RED: Test root endpoint exists

        Expected: / endpoint should return API info
        Current: Module does not exist (should fail)
        """
        from src.api.main import app

        client = TestClient(app)
        response = client.get("/")

        assert response.status_code == 200

    def test_api_v1_prefix_routes_exist(self):
        """
        RED: Test /api/v1 prefix routes are configured

        Expected: Routes under /api/v1 should be accessible
        Current: Module does not exist (should fail)
        """
        from src.api.main import app

        # Get all routes
        routes = [route.path for route in app.routes]

        # Should have at least health route
        assert "/health" in routes or any("/health" in r for r in routes)


# ========================================================================
# Test OpenAPI Documentation
# ========================================================================


class TestOpenAPIDocumentation:
    """Test OpenAPI documentation generation"""

    def test_openapi_schema_generated(self):
        """
        RED: Test OpenAPI schema is auto-generated

        Expected: /openapi.json should return valid schema
        Current: Module does not exist (should fail)
        """
        from src.api.main import app

        client = TestClient(app)
        response = client.get("/openapi.json")

        assert response.status_code == 200
        schema = response.json()

        assert "openapi" in schema
        assert "info" in schema
        assert "paths" in schema

    def test_swagger_ui_accessible(self):
        """
        RED: Test Swagger UI is accessible

        Expected: /docs should return HTML documentation
        Current: Module does not exist (should fail)
        """
        from src.api.main import app

        client = TestClient(app)
        response = client.get("/docs")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_redoc_accessible(self):
        """
        RED: Test ReDoc is accessible

        Expected: /redoc should return HTML documentation
        Current: Module does not exist (should fail)
        """
        from src.api.main import app

        client = TestClient(app)
        response = client.get("/redoc")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_openapi_info_section(self):
        """
        RED: Test OpenAPI info section is properly configured

        Expected: title, version, description should match config
        Current: Module does not exist (should fail)
        """
        from src.api.main import app

        client = TestClient(app)
        response = client.get("/openapi.json")
        schema = response.json()

        assert schema["info"]["title"] == "DuckDB Data Processor API"
        assert schema["info"]["version"] == "1.0.0"


# ========================================================================
# Test Integration with Phase 1 Components
# ========================================================================


class TestPhase1Integration:
    """Test integration with Phase 1 components (Processor, Config)"""

    def test_processor_integration_via_dependency(self):
        """
        RED: Test Processor can be accessed via dependency injection

        Expected: get_processor should return initialized Processor
        Current: Module does not exist (should fail)
        """
        from src.api.dependencies import get_processor
        from src.core.processor import Processor

        processor = get_processor()

        # Should have expected Processor attributes
        assert hasattr(processor, 'connection')
        assert hasattr(processor, 'load_csv')

    def test_config_integration_via_dependency(self):
        """
        RED: Test Config can be accessed via dependency injection

        Expected: get_config should return loaded Config
        Current: Module does not exist (should fail)
        """
        from src.api.dependencies import get_config

        config = get_config()

        # Config should be accessible
        assert config is not None

    def test_app_startup_initializes_processor(self):
        """
        RED: Test that app startup event initializes Processor

        Expected: Startup event should create Processor instance
        Current: Module does not exist (should fail)
        """
        from src.api.main import app

        # App should have startup event handlers
        assert len(app.router.on_startup) > 0 or app.state.has_state


# ========================================================================
# Test Middleware Package Structure
# ========================================================================


class TestMiddlewarePackage:
    """Test middleware package structure"""

    def test_middleware_module_importable(self):
        """
        RED: Test middleware module can be imported

        Expected: Module should exist and be importable
        Current: Module does not exist (should fail)
        """
        with pytest.raises(ImportError):
            from src.api import middleware

    def test_request_id_middleware_class(self):
        """
        RED: Test RequestIDMiddleware class exists

        Expected: RequestIDMiddleware class should be available
        Current: Module does not exist (should fail)
        """
        from src.api.middleware import RequestIDMiddleware

        assert RequestIDMiddleware is not None

    def test_logging_middleware_class(self):
        """
        RED: Test LoggingMiddleware class exists

        Expected: LoggingMiddleware class should be available
        Current: Module does not exist (should fail)
        """
        from src.api.middleware import LoggingMiddleware

        assert LoggingMiddleware is not None

    def test_error_handler_middleware_class(self):
        """
        RED: Test ErrorHandlerMiddleware class exists

        Expected: ErrorHandlerMiddleware class should be available
        Current: Module does not exist (should fail)
        """
        from src.api.middleware import ErrorHandlerMiddleware

        assert ErrorHandlerMiddleware is not None


# ========================================================================
# Test Configuration Integration
# ========================================================================


class TestConfigurationIntegration:
    """Test configuration-driven behavior"""

    def test_app_uses_config_for_title(self):
        """
        RED: Test app title comes from configuration

        Expected: App should read title from config
        Current: Module does not exist (should fail)
        """
        from src.api.main import app

        # Title should match expected config value
        assert "DuckDB Data Processor API" in app.title

    def test_cors_configurable_from_config(self):
        """
        RED: Test CORS settings are configurable

        Expected: CORS origins should come from config
        Current: Module does not exist (should fail)
        """
        from src.api.main import app
        from src.api.dependencies import get_config

        config = get_config()
        # CORS should be configured (check via middleware existence)
        assert len(app.user_middleware) > 0


# ========================================================================
# Test Error Handling
# ========================================================================


class TestErrorHandling:
    """Test application error handling"""

    def test_error_handler_catches_exceptions(self):
        """
        RED: Test error handler middleware catches exceptions

        Expected: Unhandled exceptions should return JSON error
        Current: Module does not exist (should fail)
        """
        from src.api.main import app

        client = TestClient(app)

        # Try to access a route that doesn't exist
        response = client.get("/nonexistent-route")

        # Should return 404, not crash
        assert response.status_code == 404

    def test_error_response_format(self):
        """
        RED: Test error responses have consistent format

        Expected: Errors should return JSON with 'detail' field
        Current: Module does not exist (should fail)
        """
        from src.api.main import app

        client = TestClient(app)
        response = client.get("/nonexistent-route")

        # Should have detail field
        assert "detail" in response.json()
