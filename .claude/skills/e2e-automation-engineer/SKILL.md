---
name: e2e-automation-engineer
description: Implement Playwright E2E tests for DuckDB workflow builder with robust test stability, proper wait strategies, and comprehensive coverage. Create automated browser tests for all node types (input, filter, aggregate, join, SQL, output), React Flow interactions, file uploads, and data validation. Use when: user mentions "E2E tests", "Playwright", "browser automation", "automated testing", "test implementation", "test automation" for web applications, workflow builders, UI testing. DOES NOT trigger for: unit test implementation, API test implementation, manual test execution, performance testing without browser automation.
---

# E2E Automation Engineer Skill

Implement reliable, flake-free Playwright E2E tests for the DuckDB workflow builder with proper test architecture and comprehensive coverage.

## Your Responsibilities

1. **Setup Playwright**: Configure test infrastructure and dependencies
2. **Create Page Objects**: Build reusable page object models
3. **Implement Tests**: Write automated tests for all test cases
4. **Ensure Stability**: Use proper waits, retries, and error handling
5. **Integrate CI/CD**: Configure test execution in pipeline

## Test Architecture

### Directory Structure
```
tests/e2e/
├── playwright.config.ts          # Test configuration
├── pages/                        # Page object models
│   ├── WorkflowCanvas.ts         # Main canvas interactions
│   ├── DataInspectionPanel.ts    # Data preview panel
│   └── AiSqlBuilderPanel.ts      # AI SQL builder panel
├── fixtures/                     # Test fixtures and helpers
│   ├── testData.ts               # Test data upload helpers
│   ├── workflows.ts              # Workflow load helpers
│   └── assertions.ts             # Custom assertion helpers
├── utils/                        # Utility functions
│   ├── selectors.ts              # CSS selector constants
│   └── waits.ts                  # Custom wait strategies
├── smoke/                        # Smoke tests
│   └── basic-workflow.spec.ts
├── nodes/                        # Node-specific tests
│   ├── input-node.spec.ts
│   ├── filter-node.spec.ts
│   ├── aggregate-node.spec.ts
│   ├── join-node.spec.ts
│   └── sql-node.spec.ts
├── workflows/                    # Multi-node workflow tests
│   └── multi-node-workflow.spec.ts
└── edge-cases/                   # Edge case tests
    ├── null-handling.spec.ts
    └── special-chars.spec.ts
```

## Playwright Configuration

### playwright.config.ts
```typescript
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : 4,
  reporter: [
    ['html'],
    ['json', { outputFile: 'test-results/results.json' }],
    ['junit', { outputFile: 'test-results/results.xml' }]
  ],
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    actionTimeout: 10000,
    navigationTimeout: 30000,
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
    timeout: 120 * 1000,
  },
});
```

## Page Object Models

### WorkflowCanvas Page Object
```typescript
// pages/WorkflowCanvas.ts
import { Page, expect } from '@playwright/test';

export class WorkflowCanvas {
  constructor(private page: Page) {}

  // Navigation
  async goto() {
    await this.page.goto('/');
    await this.waitForCanvasReady();
  }

  private async waitForCanvasReady() {
    await this.page.waitForSelector('[data-testid="workflow-canvas"]', {
      state: 'visible'
    });
  }

  // Node Operations
  async addNode(type: string, label?: string) {
    const nodePalette = `[data-testid="node-palette-${type}"]`;
    const canvas = '[data-testid="workflow-canvas"]';

    await this.page.dragAndDrop(nodePalette, canvas);

    if (label) {
      await this.configureNode(type, label);
    }
  }

  async selectNode(nodeId: string) {
    await this.page.click(`[data-testid="node-${nodeId}"]`);
  }

  async configureNode(type: string, config: Record<string, any>) {
    // Open configuration panel
    await this.page.click('[data-testid="config-panel"]');

    // Set configuration values
    for (const [key, value] of Object.entries(config)) {
      await this.page.fill(`[data-testid="config-${key}"]`, String(value));
    }
  }

  // Edge Operations
  async connectNodes(sourceId: string, targetId: string) {
    const sourceHandle = `[data-testid="node-${sourceId}"] .react-flow__handle-source`;
    const targetHandle = `[data-testid="node-${targetId}"] .react-flow__handle-target`;

    await this.page.dragAndDrop(sourceHandle, targetHandle);
  }

  // Workflow Operations
  async runWorkflow() {
    await this.page.click('[data-testid="run-workflow-button"]');
    await this.waitForExecution();
  }

  private async waitForExecution() {
    await this.page.waitForSelector('[data-testid="execution-complete"]', {
      state: 'visible',
      timeout: 30000
    });
  }

  // Data Operations
  async uploadCSV(filePath: string) {
    const fileInput = this.page.locator('input[type="file"]');
    await fileInput.setInputFiles(filePath);
    await this.waitForDataPreview();
  }

  private async waitForDataPreview() {
    await this.page.waitForSelector('[data-testid="data-preview-table"]', {
      state: 'visible'
    });
  }

  // Assertions
  async verifyRowCount(expectedCount: number) {
    const rowCount = await this.getRowCount();
    expect(rowCount).toBe(expectedCount);
  }

  async getRowCount(): Promise<number> {
    const rows = await this.page.locator(
      '[data-testid="data-preview-table"] tbody tr'
    ).count();
    return rows;
  }

  async verifyColumnNames(expectedColumns: string[]) {
    const columns = await this.page.locator(
      '[data-testid="data-preview-table"] thead th'
    ).allTextContents();
    expect(columns).toEqual(expectedColumns);
  }

  // Cleanup
  async clearCanvas() {
    await this.page.click('[data-testid="clear-canvas-button"]');
    await this.page.waitForSelector('[data-testid="workflow-canvas"]:empty');
  }
}
```

### DataInspectionPanel Page Object
```typescript
// pages/DataInspectionPanel.ts
import { Page, expect } from '@playwright/test';

export class DataInspectionPanel {
  constructor(private page: Page) {}

  async open() {
    await this.page.click('[data-testid="data-inspection-panel"]');
    await this.page.waitForSelector('[data-testid="data-preview-table"]', {
      state: 'visible'
    });
  }

  async getPreviewData(): Promise<string[][]> {
    const rows = await this.page.locator(
      '[data-testid="data-preview-table"] tbody tr'
    );

    const data: string[][] = [];
    const count = await rows.count();

    for (let i = 0; i < count; i++) {
      const cells = await rows.nth(i).locator('td').allTextContents();
      data.push(cells);
    }

    return data;
  }

  async verifyCellData(rowIndex: number, colIndex: number, expectedValue: string) {
    const cell = this.page.locator(
      `[data-testid="data-preview-table"] tbody tr:nth-child(${rowIndex + 1}) td:nth-child(${colIndex + 1})`
    );
    await expect(cell).toHaveText(expectedValue);
  }
}
```

## Test Fixtures

### Test Data Fixture
```typescript
// fixtures/testData.ts
import { Page } from '@playwright/test';

export class TestDataFixture {
  constructor(private page: Page) {}

  async uploadDiverseCSV() {
    const fileInput = this.page.locator('input[type="file"]');
    await fileInput.setInputFiles('./data/test_data_diverse.csv');
    await this.page.waitForSelector('[data-testid="data-preview-table"]');
  }

  async uploadJoinCSV() {
    const fileInput = this.page.locator('input[type="file"]');
    await fileInput.setInputFiles('./data/test_data_join.csv');
    await this.page.waitForSelector('[data-testid="data-preview-table"]');
  }

  async verifyFinancialSegment() {
    // Verify first 50 rows are financial data
    const rows = await this.page.locator(
      '[data-testid="data-preview-table"] tbody tr'
    );

    for (let i = 0; i < 50; i++) {
      const row = rows.nth(i);
      await expect(row.locator('td').nth(0)).toContainText('TXN');
    }
  }
}
```

### Workflow Fixture
```typescript
// fixtures/workflows.ts
import { Page } from '@playwright/test';

export class WorkflowFixture {
  constructor(private page: Page) {}

  async loadWorkflow(workflowName: string) {
    // Read workflow JSON
    const workflow = require(`../../data/workflows/${workflowName}.json`);

    // Inject workflow into application state
    await this.page.evaluate((wf) => {
      window.setWorkflow(wf);
    }, workflow);

    await this.page.waitForSelector(`[data-testid="node-${workflow.nodes[0].id}"]`);
  }

  async verifyWorkflowLoaded(expectedNodeCount: number) {
    const nodes = await this.page.locator('[data-testid^="node-"]').count();
    expect(nodes).toBe(expectedNodeCount);
  }
}
```

## Test Implementation Examples

### Smoke Test
```typescript
// smoke/basic-workflow.spec.ts
import { test, expect } from '@playwright/test';
import { WorkflowCanvas } from '../pages/WorkflowCanvas';

test.describe('Smoke Tests', () => {
  test('basic workflow execution', async ({ page }) => {
    const canvas = new WorkflowCanvas(page);

    await canvas.goto();
    await canvas.uploadCSV('./data/test_data_diverse.csv');
    await canvas.addNode('filter', { condition: 'amount > 1000' });
    await canvas.runWorkflow();
    await canvas.verifyRowCount(50);
  });
});
```

### Filter Node Test
```typescript
// nodes/filter-node.spec.ts
import { test, expect } from '@playwright/test';
import { WorkflowCanvas } from '../pages/WorkflowCanvas';

test.describe('Filter Node', () => {
  test.beforeEach(async ({ page }) => {
    const canvas = new WorkflowCanvas(page);
    await canvas.goto();
    await canvas.uploadCSV('./data/test_data_diverse.csv');
  });

  test('filters by single condition', async ({ page }) => {
    const canvas = new WorkflowCanvas(page);
    await canvas.addNode('filter', { condition: 'amount > 1000' });
    await canvas.runWorkflow();
    await canvas.verifyRowCount(50);
  });

  test('filters by multiple conditions', async ({ page }) => {
    const canvas = new WorkflowCanvas(page);
    await canvas.addNode('filter', {
      condition: 'amount > 1000 AND status = "active"'
    });
    await canvas.runWorkflow();
    const rowCount = await canvas.getRowCount();
    expect(rowCount).toBeLessThan(50);
  });

  test('handles null values in filter', async ({ page }) => {
    const canvas = new WorkflowCanvas(page);
    await canvas.addNode('filter', { condition: 'amount IS NOT NULL' });
    await canvas.runWorkflow();
    await canvas.verifyRowCount(180);
  });
});
```

### Edge Case Test
```typescript
// edge-cases/null-handling.spec.ts
import { test, expect } from '@playwright/test';
import { WorkflowCanvas } from '../pages/WorkflowCanvas';

test.describe('Null Handling', () => {
  test('aggregate ignores null values', async ({ page }) => {
    const canvas = new WorkflowCanvas(page);
    await canvas.goto();
    await canvas.uploadCSV('./data/test_data_diverse.csv');
    await canvas.addNode('aggregate', {
      groupBy: ['account_type'],
      aggregations: [
        { column: 'amount', function: 'sum', alias: 'total' }
      ]
    });
    await canvas.runWorkflow();
    await canvas.verifyRowCount(5);
  });

  test('filter handles null values', async ({ page }) => {
    const canvas = new WorkflowCanvas(page);
    await canvas.goto();
    await canvas.uploadCSV('./data/test_data_diverse.csv');
    await canvas.addNode('filter', { condition: 'amount > 0' });
    await canvas.runWorkflow();
    const rows = await canvas.page.locator(
      '[data-testid="data-preview-table"] tbody tr td:nth-child(2)'
    ).allTextContents();
    expect(rows.every(row => row !== '')).toBe(true);
  });
});
```

## Best Practices

### 1. Use Data-TestID Selectors
```typescript
// Good
await page.click('[data-testid="run-button"]');

// Avoid
await page.click('button:text("Run")');
```

### 2. Explicit Waits
```typescript
// Good
await page.waitForSelector('[data-testid="results"]');
await expect(page.locator('[data-testid="results"]')).toBeVisible();

// Avoid
await page.waitForTimeout(5000);
```

### 3. Proper Assertions
```typescript
// Good
await expect(page.locator('[data-testid="row-count"]')).toHaveText('100');

// Avoid
const text = await page.locator('[data-testid="row-count"]').textContent();
expect(text).toBe('100');
```

### 4. Handle Race Conditions
```typescript
// Good
await Promise.all([
  page.waitForNavigation(),
  page.click('[data-testid="submit"]')
]);
```

### 5. Retry Mechanisms
```typescript
async retryOperation<T>(
  operation: () => Promise<T>,
  maxRetries = 3
): Promise<T> {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await operation();
    } catch (error) {
      if (i === maxRetries - 1) throw error;
      await this.page.waitForTimeout(1000);
    }
  }
  throw new Error('Max retries exceeded');
}
```

## Implementation Steps

1. **Setup Playwright**: Install dependencies, create config
2. **Create Page Objects**: Build reusable page models
3. **Create Fixtures**: Build test data and workflow helpers
4. **Implement Smoke Tests**: Basic functionality tests
5. **Implement Node Tests**: Tests for each node type
6. **Implement Edge Case Tests**: Null handling, special chars
7. **Implement Workflow Tests**: Multi-node scenarios
8. **Configure CI/CD**: Setup test pipeline integration
9. **Generate Reports**: HTML and JSON test reports

## File Output

### Configuration
- `tests/e2e/playwright.config.ts`
- `tests/e2e/package.json` (if needed)

### Page Objects
- `tests/e2e/pages/WorkflowCanvas.ts`
- `tests/e2e/pages/DataInspectionPanel.ts`
- `tests/e2e/pages/AiSqlBuilderPanel.ts`

### Fixtures
- `tests/e2e/fixtures/testData.ts`
- `tests/e2e/fixtures/workflows.ts`
- `tests/e2e/fixtures/assertions.ts`

### Tests
- `tests/e2e/smoke/basic-workflow.spec.ts`
- `tests/e2e/nodes/{node-type}.spec.ts`
- `tests/e2e/workflows/multi-node.spec.ts`
- `tests/e2e/edge-cases/{edge-case}.spec.ts`

## Quality Checks

Before finalizing tests:
- [ ] All tests are deterministic (no random failures)
- [ ] Tests are isolated (can run in any order)
- [ ] Tests are fast (< 10s per test)
- [ ] Proper cleanup after each test
- [ ] Meaningful assertion messages
- [ ] No hardcoded timeouts (use explicit waits)
- [ ] Data-testid selectors are used
- [ ] Error handling is robust

## Error Handling

**If test is flaky:**
- Add explicit waits using `waitForSelector`
- Use `waitFor()` instead of hardcoded timeouts
- Check for race conditions in async operations
- Add retry mechanisms for transient failures

**If selector is unstable:**
- Use data-testid attributes
- Add stable CSS selectors
- Avoid using text content as selectors
- Use relative selectors (parent, child, sibling)

**If test data is missing:**
- Coordinate with test-data-architect
- Create minimal test data inline
- Document data requirements clearly

**If browser automation fails:**
- Log screenshots/videos for debugging
- Capture console errors
- Continue with remaining tests
- Report specific failure details

## Communication Protocol

**Send To:**
- **e2e-orchestrator**: Test implementation progress, issues, results
- **test-case-strategist**: Test feasibility feedback, automation gaps
- **test-data-architect**: Data upload requirements, file path validation

**Receive From:**
- **e2e-orchestrator**: Test implementation task assignments
- **test-case-strategist**: Test case specifications to implement
- **test-data-architect**: Test data file locations and metadata

## CI/CD Integration

### GitHub Actions Example
```yaml
name: E2E Tests

on:
  push:
    branches: [main]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - run: npm ci
      - run: npx playwright install --with-deps
      - run: npm run test:e2e
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: playwright-report
          path: test-results/
```

## Why This Matters

Reliable E2E tests are the foundation of confidence in deployment. Well-architected tests with proper page objects, stable selectors, and robust error handling prevent false negatives and catch real bugs. Good test automation:

1. **Prevents Regressions**: Catches bugs before production
2. **Enables Refactoring**: Confidence to change code safely
3. **Documents Behavior**: Tests serve as living documentation
4. **Speeds Development**: Fast feedback on changes
