# E2E Test Implementation Guide

**Version**: 1.0.0
**Last Updated**: 2026-04-04

## Overview

This guide provides detailed implementation instructions for the 58 E2E test cases designed in `test_cases_design.md`. Tests are implemented using Playwright (TypeScript) for UI workflows and Pytest (Python) for API-based tests.

## Test File Structure

```
tests/e2e/
├── playwright.config.ts          # Playwright configuration
├── test_cases_design.md          # Test case specifications
├── test_implementation_guide.md  # This file
├── generate_test_data.py         # Test data generator
├── test_data/                    # Generated test fixtures
│   ├── sales.csv
│   ├── customers.csv
│   ├── orders.csv
│   ├── edge_cases.csv
│   └── ...
├── page-objects/                 # Page Object Model classes
│   ├── BasePage.ts
│   ├── CanvasPage.ts
│   ├── DataPanelPage.ts
│   └── WorkflowBuilderPage.ts
├── helpers/                      # Test helper functions
│   ├── data-helpers.ts
│   ├── workflow-helpers.ts
│   └── assertion-helpers.ts
├── smoke/                        # Smoke tests (5 tests)
│   ├── app-load.spec.ts
│   ├── file-upload.spec.ts
│   └── simple-workflow.spec.ts
├── nodes/                        # Node-specific tests
│   ├── input-node.spec.ts        # Input node tests (8)
│   ├── filter-node.spec.ts       # Filter node tests (10)
│   ├── aggregate-node.spec.ts    # Aggregate node tests (8)
│   ├── join-node.spec.ts         # Join/combine tests (7)
│   ├── sql-node.spec.ts          # SQL node tests (10)
│   └── output-node.spec.ts       # Output node tests (5)
├── workflows/                    # Multi-node workflow tests
│   ├── basic-workflows.spec.ts   # Happy path workflows
│   └── complex-workflows.spec.ts # 10+ node pipelines
├── edge-cases/                   # Edge case tests (8)
│   ├── circular-dependency.spec.ts
│   ├── orphaned-nodes.spec.ts
│   └── invalid-data.spec.ts
├── performance/                  # Performance tests (5)
│   ├── large-files.spec.ts
│   └── concurrent-execution.spec.ts
└── api/                          # API-level tests (Python)
    ├── test_workflow_execution.py
    └── test_report_builder.py
```

## Test Implementation Matrix

### Smoke Tests (5 tests)

| Test ID | File | Function Name | Status |
|---------|------|---------------|--------|
| SMOKE-001 | smoke/app-load.spec.ts | testApplicationLoad | TODO |
| SMOKE-002 | smoke/file-upload.spec.ts | testFileUpload | TODO |
| SMOKE-003 | smoke/simple-workflow.spec.ts | testSimpleWorkflow | TODO |
| SMOKE-004 | smoke/simple-workflow.spec.ts | testFilterWorkflow | TODO |
| SMOKE-005 | smoke/simple-workflow.spec.ts | testSqlWorkflow | TODO |

### Input Node Tests (8 tests)

| Test ID | File | Function Name | Status |
|---------|------|---------------|--------|
| INP-001 | nodes/input-node.spec.ts | testCsvUploadBasic | TODO |
| INP-002 | nodes/input-node.spec.ts | testCsvUploadEmpty | TODO |
| INP-003 | nodes/input-node.spec.ts | testCsvUploadLarge | TODO |
| INP-004 | nodes/input-node.spec.ts | testCsvUploadSpecialChars | TODO |
| INP-005 | nodes/input-node.spec.ts | testCsvUploadNoHeader | TODO |
| INP-006 | nodes/input-node.spec.ts | testExcelUpload | TODO |
| INP-007 | nodes/input-node.spec.ts | testExcelUploadMultipleSheets | TODO |
| INP-008 | nodes/input-node.spec.ts | testFileUploadInvalidFormat | TODO |

### Filter Node Tests (10 tests)

| Test ID | File | Function Name | Status |
|---------|------|---------------|--------|
| FLT-001 | nodes/filter-node.spec.ts | testFilterGreaterThan | TODO |
| FLT-002 | nodes/filter-node.spec.ts | testFilterLessThan | TODO |
| FLT-003 | nodes/filter-node.spec.ts | testFilterEquals | TODO |
| FLT-004 | nodes/filter-node.spec.ts | testFilterNotEquals | TODO |
| FLT-005 | nodes/filter-node.spec.ts | testFilterContains | TODO |
| FLT-006 | nodes/filter-node.spec.ts | testFilterNotContains | TODO |
| FLT-007 | nodes/filter-node.spec.ts | testFilterStartsWith | TODO |
| FLT-008 | nodes/filter-node.spec.ts | testFilterNullValues | TODO |
| FLT-009 | nodes/filter-node.spec.ts | testFilterDateRange | TODO |
| FLT-010 | nodes/filter-node.spec.ts | testFilterEmptyResult | TODO |

### Aggregate Node Tests (8 tests)

| Test ID | File | Function Name | Status |
|---------|------|---------------|--------|
| AGG-001 | nodes/aggregate-node.spec.ts | testSumAggregation | TODO |
| AGG-002 | nodes/aggregate-node.spec.ts | testCountAggregation | TODO |
| AGG-003 | nodes/aggregate-node.spec.ts | testAvgAggregation | TODO |
| AGG-004 | nodes/aggregate-node.spec.ts | testMinMaxAggregation | TODO |
| AGG-005 | nodes/aggregate-node.spec.ts | testGroupBySingleColumn | TODO |
| AGG-006 | nodes/aggregate-node.spec.ts | testGroupByMultipleColumns | TODO |
| AGG-007 | nodes/aggregate-node.spec.ts | testAggregateWithFilter | TODO |
| AGG-008 | nodes/aggregate-node.spec.ts | testAggregateNullHandling | TODO |

### Join/Combine Node Tests (7 tests)

| Test ID | File | Function Name | Status |
|---------|------|---------------|--------|
| JIN-001 | nodes/join-node.spec.ts | testInnerJoin | TODO |
| JIN-002 | nodes/join-node.spec.ts | testLeftJoin | TODO |
| JIN-003 | nodes/join-node.spec.ts | testUnionCombine | TODO |
| JIN-004 | nodes/join-node.spec.ts | testJoinNoMatches | TODO |
| JIN-005 | nodes/join-node.spec.ts | testJoinMultipleMatches | TODO |
| JIN-006 | nodes/join-node.spec.ts | testJoinNullKeyValues | TODO |
| JIN-007 | nodes/join-node.spec.ts | testSelfJoin | TODO |

### SQL Node Tests (10 tests)

| Test ID | File | Function Name | Status |
|---------|------|---------------|--------|
| SQL-001 | nodes/sql-node.spec.ts | testBasicSelect | TODO |
| SQL-002 | nodes/sql-node.spec.ts | testSelectWithWhere | TODO |
| SQL-003 | nodes/sql-node.spec.ts | testGroupByWithHaving | TODO |
| SQL-004 | nodes/sql-node.spec.ts | testJoinInSQL | TODO |
| SQL-005 | nodes/sql-node.spec.ts | testSubquery | TODO |
| SQL-006 | nodes/sql-node.spec.ts | testWindowFunction | TODO |
| SQL-007 | nodes/sql-node.spec.ts | testCTE | TODO |
| SQL-008 | nodes/sql-node.spec.ts | testCaseWhen | TODO |
| SQL-009 | nodes/sql-node.spec.ts | testMultipleStatements | TODO |
| SQL-010 | nodes/sql-node.spec.ts | testInvalidSqlHandling | TODO |

### Output Node Tests (5 tests)

| Test ID | File | Function Name | Status |
|---------|------|---------------|--------|
| OUT-001 | nodes/output-node.spec.ts | testCsvExport | TODO |
| OUT-002 | nodes/output-node.spec.ts | testJsonExport | TODO |
| OUT-003 | nodes/output-node.spec.ts | testExcelExport | TODO |
| OUT-004 | nodes/output-node.spec.ts | testLargeDatasetExport | TODO |
| OUT-005 | nodes/output-node.spec.ts | testPreviewLimit | TODO |

### Edge Cases & Negative Tests (8 tests)

| Test ID | File | Function Name | Status |
|---------|------|---------------|--------|
| EDGE-001 | edge-cases/circular-dependency.spec.ts | testCircularDependency | TODO |
| EDGE-002 | edge-cases/orphaned-nodes.spec.ts | testOrphanedNode | TODO |
| EDGE-003 | edge-cases/invalid-data.spec.ts | testMissingRequiredField | TODO |
| EDGE-004 | edge-cases/invalid-data.spec.ts | testInvalidColumnReference | TODO |
| EDGE-005 | edge-cases/invalid-data.spec.ts | testDivisionByZero | TODO |
| EDGE-006 | edge-cases/invalid-data.spec.ts | testMemoryLimit | TODO |
| EDGE-007 | performance/concurrent-execution.spec.ts | testConcurrentWorkflowExecution | TODO |
| EDGE-008 | edge-cases/invalid-data.spec.ts | testNetworkTimeout | TODO |

### Performance Tests (5 tests)

| Test ID | File | Function Name | Status |
|---------|------|---------------|--------|
| PERF-001 | performance/large-files.spec.ts | testLargeFileProcessing | TODO |
| PERF-002 | workflows/complex-workflows.spec.ts | testComplexWorkflow | TODO |
| PERF-003 | workflows/complex-workflows.spec.ts | testMultipleFilters | TODO |
| PERF-004 | performance/large-files.spec.ts | testMemoryUsage | TODO |
| PERF-005 | performance/concurrent-execution.spec.ts | testConcurrentUsers | TODO |

## Test Implementation Template

### Playwright Test Template

```typescript
// tests/e2e/nodes/filter-node.spec.ts
import { test, expect } from '@playwright/test';
import { CanvasPage } from '../page-objects/CanvasPage';
import { DataPanelPage } from '../page-objects/DataPanelPage';
import { WorkflowBuilderPage } from '../page-objects/WorkflowBuilderPage';
import { uploadTestFile, getTestFilePath } from '../helpers/data-helpers';

test.describe('Filter Node Tests', () => {
  let canvasPage: CanvasPage;
  let dataPanel: DataPanelPage;
  let workflowBuilder: WorkflowBuilderPage;

  test.beforeEach(async ({ page }) => {
    canvasPage = new CanvasPage(page);
    dataPanel = new DataPanelPage(page);
    workflowBuilder = new WorkflowBuilderPage(page);

    // Navigate to app
    await page.goto('/');
    await canvasPage.waitForCanvasReady();
  });

  test('FLT-001: Filter - Greater Than', async ({ page }) => {
    // Arrange: Upload test data
    const filePath = getTestFilePath('sales.csv');
    await dataPanel.uploadFile(filePath);
    await dataPanel.waitForDataLoaded();

    // Act: Build workflow - Input -> Filter -> Output
    await workflowBuilder.dragNodeToCanvas('input', 100, 100);
    await workflowBuilder.dragNodeToCanvas('filter', 100, 300);
    await workflowBuilder.dragNodeToCanvas('output', 100, 500);

    // Connect nodes
    await workflowBuilder.connectNodes('input-1', 'filter-1');
    await workflowBuilder.connectNodes('filter-1', 'output-1');

    // Configure filter
    await workflowBuilder.selectNode('filter-1');
    await workflowBuilder.setFilterColumn('quantity');
    await workflowBuilder.setFilterOperator('>');
    await workflowBuilder.setFilterValue('10');

    // Execute workflow
    await workflowBuilder.executeWorkflow();

    // Assert: Verify filtered results
    const result = await workflowBuilder.getExecutionResults();
    expect(result.rowCount).toBeGreaterThan(0);
    expect(result.rowCount).toBeLessThan(1000); // Some rows filtered out

    // Verify all quantities are > 10
    const previewData = await workflowBuilder.getPreviewData();
    for (const row of previewData) {
      expect(parseInt(row.quantity)).toBeGreaterThan(10);
    }
  });
});
```

### Pytest Test Template

```python
# tests/e2e/api/test_filter_node.py
import pytest
import httpx
from helpers.data_helpers import get_test_file_path, upload_file
from helpers.workflow_helpers import build_workflow, execute_workflow

@pytest.mark.asyncio
@pytest.mark.filter
async def test_filter_greater_than():
    """FLT-001: Filter - Greater Than"""
    async with httpx.AsyncClient(base_url="http://localhost:8000/api/v1", timeout=30.0) as client:
        # Arrange: Upload test data
        file_path = get_test_file_path('sales.csv')
        upload_response = await upload_file(client, file_path)
        assert upload_response.status_code == 200
        file_data = upload_response.json()

        # Act: Build workflow - Input -> Filter -> Output
        nodes = [
            {
                "id": "input_1",
                "type": "input",
                "data": {
                    "label": "Sales Data",
                    "config": {
                        "file_path": file_data["file_path"],
                        "availableColumns": ["id", "product", "category", "quantity", "price", "date"]
                    }
                }
            },
            {
                "id": "filter_1",
                "type": "default",
                "data": {
                    "label": "Filter Records",
                    "subtype": "filter",
                    "config": {
                        "column": "quantity",
                        "operator": ">",
                        "value": "10",
                        "availableColumns": ["id", "product", "category", "quantity", "price", "date"]
                    }
                }
            },
            {
                "id": "output_1",
                "type": "output",
                "data": {
                    "label": "Export",
                    "config": {
                        "exportFormat": "csv",
                        "fileName": "filtered.csv"
                    }
                }
            }
        ]

        edges = [
            {"id": "e1", "source": "input_1", "target": "filter_1"},
            {"id": "e2", "source": "filter_1", "target": "output_1"}
        ]

        # Execute workflow
        response = await execute_workflow(client, nodes, edges)
        assert response.status_code == 200
        result = response.json()

        # Assert: Verify results
        assert result["row_count"] > 0
        assert result["row_count"] < 1000  # Some rows filtered

        # Verify all quantities > 10
        for row in result["preview"]:
            assert int(row["quantity"]) > 10
```

## Helper Functions

### data-helpers.ts

```typescript
// tests/e2e/helpers/data-helpers.ts
import path from 'path';

const TEST_DATA_DIR = path.join(__dirname, '..', 'test_data');

export function getTestFilePath(filename: string): string {
  return path.join(TEST_DATA_DIR, filename);
}

export async function uploadTestFile(page: Page, filename: string): Promise<void> {
  const fileInput = await page.locator('input[type="file"]');
  await fileInput.setInputFiles(getTestFilePath(filename));
}

export function getExpectedRowCount(filename: string, filter?: any): number {
  // Map test files to expected row counts
  const rowCounts: Record<string, number> = {
    'sales.csv': 1000,
    'customers.csv': 500,
    'orders.csv': 2000,
    'edge_cases.csv': 100,
  };

  // Apply filter logic for expected results
  // This is a simplified example
  return rowCounts[filename] || 0;
}
```

### workflow-helpers.ts

```typescript
// tests/e2e/helpers/workflow-helpers.ts
export async function buildFilterWorkflow(
  page: Page,
  inputFile: string,
  filterColumn: string,
  operator: string,
  value: string
): Promise<void> {
  // Implementation for building filter workflow
}

export async function executeWorkflow(page: Page): Promise<any> {
  const executeButton = page.locator('[data-testid="execute-workflow"]');
  await executeButton.click();

  // Wait for execution to complete
  await page.waitForSelector('[data-testid="execution-complete"]', { timeout: 30000 });

  // Get results
  const results = await page.evaluate(() => {
    return window.__workflow_results__;
  });

  return results;
}
```

## Running Tests

### Run All Tests
```bash
npm run test:e2e
```

### Run Specific Test Suite
```bash
# Smoke tests only
npm run test:e2e -- --grep @smoke

# Filter node tests only
npm run test:e2e -- nodes/filter-node.spec.ts

# Specific test case
npm run test:e2e -- --grep "FLT-001"
```

### Run with Debugging
```bash
# Run with headed browser
npm run test:e2e -- --headed

# Run with debug mode
npm run test:e2e -- --debug

# Run specific test with debug
npm run test:e2e -- --debug --grep "FLT-001"
```

## Test Data Management

### Generate Test Data
```bash
# Generate all test data
python3 tests/e2e/generate_test_data.py

# Generate large datasets for performance tests
python3 tests/e2e/generate_test_data.py --large
```

### Test Data Cleanup
```bash
# Clean generated test data
rm -rf tests/e2e/test_data/*.csv
```

## CI/CD Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/e2e-tests.yml
name: E2E Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  e2e-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '20'
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          npm ci
          pip install -r requirements.txt
      - name: Generate test data
        run: python3 tests/e2e/generate_test_data.py
      - name: Install Playwright browsers
        run: npx playwright install --with-deps
      - name: Run E2E tests
        run: npm run test:e2e
      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: test-results
          path: |
            test-results/
            playwright-report/
```

## Test Reporting

### HTML Report
```bash
npm run test:e2e -- --reporter=html
# Open: playwright-report/index.html
```

### JSON Report
```bash
npm run test:e2e -- --reporter=json
# Output: test-results/results.json
```

### JUnit Report
```bash
npm run test:e2e -- --reporter=junit
# Output: test-results/results.xml
```

## Best Practices

1. **Test Isolation**: Each test should be independent and clean up after itself
2. **Wait Strategies**: Use explicit waits over implicit waits
3. **Assertions**: Use specific assertions with clear error messages
4. **Test Data**: Use generated test data, don't rely on external sources
5. **Page Objects**: Use Page Object Model for maintainable tests
6. **Retry Logic**: Configure retries for flaky tests, but fix the root cause
7. **Parallel Execution**: Design tests to run in parallel without conflicts
8. **Documentation**: Add clear comments explaining complex test logic

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| Test data not found | Run `python3 tests/e2e/generate_test_data.py` |
| Timeout errors | Increase timeout in playwright.config.ts |
| Flaky tests | Add proper waits, check for element visibility |
| Browser not launching | Run `npx playwright install` |
| Port already in use | Kill process using port 3000 |

## Progress Tracking

Track implementation progress using the test case IDs:

- [ ] Phase 1: Smoke Tests (5/58)
- [ ] Phase 2: Core Functionality (30/58)
- [ ] Phase 3: Edge Cases & Performance (23/58)

Update this document as tests are implemented by changing `TODO` to `DONE` in the status column.
