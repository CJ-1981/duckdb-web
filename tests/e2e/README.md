# E2E Tests

End-to-end tests for DuckDB Web using Playwright.

## Setup

Install dependencies:
```bash
npm install
```

Install Playwright browsers:
```bash
npx playwright install chromium
```

## Running Tests

Run all E2E tests:
```bash
npm run test:e2e
```

Run tests in UI mode (interactive):
```bash
npm run test:e2e:ui
```

Run tests in debug mode:
```bash
npm run test:e2e:debug
```

Run tests in headed mode (see browser):
```bash
npm run test:e2e:headed
```

View test report:
```bash
npm run test:e2e:report
```

## Test Structure

```
tests/e2e/
├── playwright.config.ts    # Playwright configuration
├── pages/                  # Page Object Models
│   ├── WorkflowCanvas.ts
│   └── DataInspectionPanel.ts
├── fixtures/              # Test data and helpers
│   └── testData.ts
├── smoke.spec.ts          # Smoke tests
├── canvas-nodes.spec.ts   # Node and canvas tests
├── edge-cases.spec.ts     # Edge case handling tests
└── data-inspection.spec.ts # Data inspection panel tests
```

## Test Categories

### Smoke Tests (`smoke.spec.ts`)
Basic functionality verification:
- Application loads
- Canvas operations
- Node addition/removal
- File upload
- Basic workflow execution

### Canvas and Node Tests (`canvas-nodes.spec.ts`)
Node-specific functionality:
- Input node configuration
- Filter node configuration
- Aggregate node configuration
- Join node configuration
- Output node configuration
- Node connections
- Node operations (delete, duplicate)

### Edge Cases Tests (`edge-cases.spec.ts`)
Edge case handling:
- Null values
- Special characters
- Empty files
- Malformed CSV
- Different date formats
- Unicode characters
- Large datasets
- Duplicate columns

### Data Inspection Tests (`data-inspection.spec.ts`)
Data inspection panel:
- Data table display
- Schema view
- Statistics computation
- Format copying
- Full dataset analysis

## Page Objects

### WorkflowCanvas
Handles all canvas-related operations:
- Node dragging and dropping
- Node selection and deletion
- Node connections
- Workflow execution
- Canvas navigation (zoom, pan)

### DataInspectionPanel
Handles data inspection:
- Data table viewing
- Schema inspection
- Statistics viewing
- Format copying (MD, JSON, SQL)

## Test Fixtures

### Test Data
Predefined CSV test datasets:
- `sampleCsvData` - Basic user data
- `csvWithNulls` - Data with null values
- `csvWithSpecialChars` - Data with special characters
- `ordersData` - Order data for joins
- `salesData` - Sales data for aggregation

### Helper Functions
- `uploadTestCsv(page, testData)` - Upload a test CSV file
- `dragAndDropCsv(page, testData)` - Drag and drop CSV upload
- `getAllTestDatasets()` - Get all available test datasets
- `getTestDataset(name)` - Get a specific dataset

## Configuration

The Playwright configuration is in `playwright.config.ts`:

- **Browser**: Chrome only (for consistency)
- **Base URL**: `http://localhost:3000`
- **Test directory**: `./tests/e2e`
- **Workers**: 4 (local), 1 (CI)
- **Retries**: 0 (local), 2 (CI)
- **Reports**: HTML, JSON, JUnit, List

## Writing New Tests

1. Create a new test file in `tests/e2e/`
2. Import necessary page objects and fixtures
3. Use the test.describe/test syntax:

```typescript
import { test, expect } from '@playwright/test';
import { WorkflowCanvas } from './pages/WorkflowCanvas';
import { DataInspectionPanel } from './pages/DataInspectionPanel';

test.describe('My Feature Tests', () => {
  test('does something', async ({ page }) => {
    const canvas = new WorkflowCanvas(page);
    const panel = new DataInspectionPanel(page);

    await page.goto('');
    await canvas.waitForReady();

    // Your test code here
    await expect(something).toBeVisible();
  });
});
```

## Best Practices

1. **Use Page Objects**: Always use page objects for interacting with UI elements
2. **Wait for Ready**: Always call `waitForReady()` after navigation
3. **Explicit Waits**: Use explicit waits with expect instead of fixed timeouts
4. **Deterministic Tests**: Ensure tests are deterministic and can run in parallel
5. **Cleanup**: Each test should clean up after itself
6. **Descriptive Names**: Use descriptive test names that explain what is being tested
7. **Test Isolation**: Tests should not depend on each other

## Debugging

### Debug Mode
Run tests in debug mode to step through tests:
```bash
npm run test:e2e:debug
```

### Screenshots and Videos
Screenshots and videos are automatically captured on failures in the `test-results` directory.

### Trace Files
Trace files are retained on failures. View them with:
```bash
npx playwright show-trace trace.zip
```

### headed Mode
Run tests in headed mode to see the browser:
```bash
npm run test:e2e:headed
```

## CI/CD Integration

Tests run automatically in CI with:
- Single worker (no parallelism)
- 2 retries on failure
- Full reporting (HTML, JSON, JUnit)

## Troubleshooting

### Tests Time Out
- Increase timeout in `playwright.config.ts`
- Check if the dev server is running
- Verify the base URL is correct

### Flaky Tests
- Check for race conditions
- Use explicit waits instead of fixed timeouts
- Ensure tests are isolated

### Browser Not Found
- Install Playwright browsers: `npx playwright install chromium`
