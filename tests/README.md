# Test Suite for DuckDB Data Processor

## Overview

This directory contains the comprehensive test suite for the DuckDB Data Processor - a full-stack data analysis platform powered by DuckDB, FastAPI, and Next.js.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Next.js Frontend                        │
│              (React 19, Tailwind CSS, shadcn/ui)           │
│  - Workflow Canvas, Data Inspection, AI SQL Builder        │
└───────────────────────┬─────────────────────────────────────┘
                        │ REST API
┌───────────────────────▼─────────────────────────────────────┐
│                    FastAPI Backend                          │
│              (Python 3.13+, Pydantic v2)                    │
│  - CSV/JSON connectors, DuckDB processor, Workflow engine  │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│                    DuckDB Database                          │
│           (In-memory analytical database)                   │
└─────────────────────────────────────────────────────────────┘
```

## Test Organization

```
tests/
├── unit/                   # Python unit tests (pytest)
│   ├── test_csv_connector.py
│   ├── test_database_connector.py
│   ├── test_processor.py
│   ├── test_sql_cache.py
│   ├── test_error_mapping.py
│   ├── test_config.py
│   └── core/processor/test_streaming.py
│
├── integration/            # Integration tests
│   ├── test_csv_processing.py
│   ├── test_processor_workflow.py
│   ├── test_celery.py
│   ├── test_mysql_connector.py
│   └── test_postgresql_connector.py
│
├── e2e/                   # End-to-end tests (Playwright)
│   ├── smoke/             # Basic workflow tests
│   ├── nodes/             # Node-specific tests
│   ├── edge-cases/        # Null handling, special chars
│   ├── pages/             # Page objects
│   └── fixtures/          # Test data & helpers
│
├── api/                   # API endpoint tests
│   ├── test_workflows.py
│   ├── test_jobs.py
│   ├── test_users.py
│   ├── test_auth.py
│   └── test_rbac.py
│
├── performance/           # Performance benchmarks
│   ├── test_caching.py
│   └── test_streaming.py
│
└── security/              # Security tests
    └── test_injection.py
```

## Running Tests

### Python Tests (pytest)

```bash
# Run all Python tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html --cov-report=term

# Run specific test file
pytest tests/unit/test_csv_connector.py -v

# Run specific test
pytest tests/unit/test_csv_connector.py::TestCSVConnector::test_load_csv -v

# Run with verbose output
pytest tests/ -vv

# Run and stop on first failure
pytest tests/ -x

# Run only unit tests
pytest tests/unit/ -v

# Run only integration tests
pytest tests/integration/ -v
```

### E2E Tests (Playwright)

```bash
# Install Playwright browsers (first time only)
npx playwright install --with-deps

# Run all E2E tests
npm run test:e2e

# Run specific E2E test file
npx playwright tests/e2e/smoke/basic-workflow.spec.ts

# Run E2E tests in headed mode (see browser)
npx playwright tests/e2e/smoke/basic-workflow.spec.ts --headed

# Run E2E tests with debug mode
npx playwright tests/e2e/smoke/basic-workflow.spec.ts --debug

# Run E2E tests on specific browser
npx playwright tests/e2e/ --project=chromium
npx playwright tests/e2e/ --project=firefox
npx playwright tests/e2e/ --project=webkit
```

### API Tests

```bash
# Run API endpoint tests
pytest tests/api/ -v

# Run specific API test
pytest tests/api/test_workflows.py -v
```

## Coverage Requirements

- **Overall**: 85%+ coverage target
- **Per Module**: 80%+ minimum
- **Critical Paths**: 100% (data connectors, processor core)

## Test Dependencies

### Python Tests
```bash
# Core testing framework
pytest>=7.4.0
pytest-cov>=4.1.0
pytest-asyncio>=0.21.0
pytest-mock>=3.11.0

# Coverage
pytest-cov>=4.1.0

# Performance
pytest-benchmark>=4.0.0
```

### E2E Tests
```json
{
  "@playwright/test": "^1.40.0",
  "@types/node": "^20.0.0"
}
```

## CI/CD Integration

### GitHub Actions Workflow (`.github/workflows/e2e-tests.yml`)

Tests run automatically on:
- Every pull request
- Every push to main branch
- Before deployment

**Quality Gates**:
- ✅ All tests must pass
- ✅ Coverage must be >= 85%
- ✅ No critical security vulnerabilities
- ✅ E2E smoke tests must pass

## Test Categories

### Unit Tests (pytest)
- **Purpose**: Test individual functions and classes in isolation
- **Scope**: Single module or class
- **Speed**: Fast (milliseconds)
- **Examples**:
  - CSV connector file parsing
  - SQL query cache behavior
  - Error mapping logic
  - Configuration loading

### Integration Tests (pytest)
- **Purpose**: Test interaction between multiple components
- **Scope**: Multiple modules working together
- **Speed**: Medium (seconds)
- **Examples**:
  - CSV processing pipeline
  - Workflow execution with DuckDB
  - Database connector integration

### E2E Tests (Playwright)
- **Purpose**: Test complete user workflows in browser
- **Scope**: Full stack (frontend → backend → database)
- **Speed**: Slow (seconds to minutes)
- **Examples**:
  - Create and execute a workflow
  - Inspect data results
  - Add and connect nodes
  - Filter and aggregate data

## Current Test Status

### Unit Tests (pytest)
- **Total Tests**: 50+ tests
- **Coverage**: 75%+ (working toward 85% target)
- **Status**: ✅ Passing

### E2E Tests (Playwright)
- **Total Tests**: 15+ tests
- **Coverage**: Critical user workflows
- **Status**: ✅ Passing

### Known Test Gaps
- [ ] Additional edge case coverage for large datasets
- [ ] Performance regression tests
- [ ] Accessibility testing (a11y)
- [ ] Cross-browser compatibility matrix

## Test Naming Conventions

### Python Tests (pytest)
```python
def test_<feature>_<scenario>_<expected_outcome>(self):
    """
    GIVEN <precondition>
    WHEN <action>
    THEN <expected_result>
    """
```

**Example**:
```python
def test_csv_connector_load_valid_file_returns_dataframe(self):
    """
    GIVEN a valid CSV file with headers
    WHEN the file is loaded
    THEN a pandas DataFrame is returned with correct columns
    """
```

### E2E Tests (Playwright)
```typescript
test.describe('<Feature Name>', () => {
  test('<Scenario> <Expected Outcome>', async ({ page }) => {
    // Given
    // When
    // Then
  });
});
```

**Example**:
```typescript
test.describe('Workflow Canvas', () => {
  test('creates new workflow when user clicks add button', async ({ page }) => {
    // Given user is on workflow canvas
    // When user clicks add workflow button
    // Then new workflow appears in list
  });
});
```

## Troubleshooting

### Import Errors
**Problem**: `ImportError: No module named 'src.core.processor'`

**Solution**:
```bash
# Install the package in development mode
pip install -e .

# Or ensure PYTHONPATH includes src
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
pytest tests/
```

### Playwright Browser Issues
**Problem**: `Executable doesn't exist at /path/to/chromium`

**Solution**:
```bash
# Install Playwright browsers
npx playwright install --with-deps
```

### Database Connection Errors
**Problem**: Tests fail with database connection errors

**Solution**:
```bash
# Ensure DuckDB is installed
pip install duckdb>=0.9.0

# For PostgreSQL tests, set up test database
export TEST_DATABASE_URL="postgresql://user:pass@localhost:5432/testdb"
```

### Port Conflicts
**Problem**: Tests fail because port 8000 or 3000 is already in use

**Solution**:
```bash
# Kill processes using the ports
lsof -ti:8000 | xargs kill -9
lsof -ti:3000 | xargs kill -9

# Or use different ports in test config
export BACKEND_PORT=8001
export FRONTEND_PORT=3001
```

## Performance Benchmarks

### Current Benchmarks (tests/performance/)

| Test | Target | Current | Status |
|------|--------|---------|--------|
| CSV Loading (1MB) | < 1s | ~0.5s | ✅ |
| SQL Query Cache Hit | < 10ms | ~5ms | ✅ |
| Streaming Processing | > 1000 rows/s | ~1500 rows/s | ✅ |

## Writing New Tests

### Adding Unit Tests

1. Create test file in `tests/unit/`
2. Use pytest fixtures for setup
3. Follow naming convention
4. Add docstring with Given-When-Then

**Example**:
```python
# tests/unit/test_my_feature.py
import pytest
from src.core.processor import Processor

class TestProcessorFeature:
    def test_process_data_valid_input_returns_result(self):
        """
        GIVEN a processor with valid data
        WHEN process_data is called
        THEN correct result is returned
        """
        processor = Processor()
        data = {"col1": [1, 2, 3]}
        result = processor.process_data(data)
        assert result is not None
        assert len(result) == 3
```

### Adding E2E Tests

1. Create test file in `tests/e2e/`
2. Use Playwright page objects pattern
3. Follow naming convention
4. Use fixtures from `tests/e2e/fixtures/`

**Example**:
```typescript
// tests/e2e/features/my-feature.spec.ts
import { test, expect } from '@playwright/test';
import { WorkflowCanvas } from '../pages/WorkflowCanvas';

test.describe('My Feature', () => {
  test('does something when user interacts', async ({ page }) => {
    const canvas = new WorkflowCanvas(page);
    await canvas.goto();
    await canvas.createWorkflow();
    await expect(canvas.workflowList).toHaveCount(1);
  });
});
```

## Test Data Management

### Fixtures Location
- **Python fixtures**: `tests/conftest.py` (shared pytest fixtures)
- **E2E fixtures**: `tests/e2e/fixtures/` (test data, helpers)

### Test Data Files
- **CSV files**: `tests/e2e/fixtures/testData.csv`
- **JSON workflows**: `tests/e2e/fixtures/workflows.ts`
- **Custom data**: `tests/e2e/fixtures/testData.ts`

## Documentation References

- **Project README**: `../README.md`
- **API Documentation**: `../docs/API.md`
- **Deployment Guide**: `../docs/DEPLOYMENT.md`
- **Windows Setup**: `../docs/WINDOWS_SETUP.md`
- **Local Backend Setup**: `../docs/LOCAL_BACKEND_SETUP.md`

## Continuous Improvement

### TODO
- [ ] Increase coverage to 85%+ across all modules
- [ ] Add visual regression testing for UI
- [ ] Implement load testing for concurrent workflows
- [ ] Add accessibility (a11y) test suite
- [ ] Cross-browser testing matrix (Chrome, Firefox, Safari)
- [ ] API contract testing with OpenAPI schema validation

## Contributing

When adding new features:
1. **Write tests first** (TDD approach)
2. Ensure all tests pass before committing
3. Maintain >= 85% coverage for new code
4. Add E2E tests for user-facing features
5. Update this README if adding new test categories

## License

Copyright © 2025 DuckDB Data Processor. All rights reserved.
