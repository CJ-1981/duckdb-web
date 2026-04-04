# Playwright Setup for DuckDB Workflow Builder

## Prerequisites

### Install Playwright
```bash
npm install -D @playwright/test
npx playwright install chromium
```

### Update package.json
```json
{
  "scripts": {
    "test:e2e": "playwright test",
    "test:e2e:ui": "playwright test --ui",
    "test:e2e:debug": "playwright test --debug",
    "test:e2e:headed": "playwright test --headed"
  }
}
```

## Configuration

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

## Test Structure

### Directory Layout
```
tests/e2e/
├── playwright.config.ts
├── pages/
│   ├── WorkflowCanvas.ts
│   ├── DataInspectionPanel.ts
│   └── AiSqlBuilderPanel.ts
├── fixtures/
│   ├── testData.ts
│   └── workflows.ts
├── smoke/
│   └── basic-workflow.spec.ts
├── nodes/
│   ├── input-node.spec.ts
│   ├── filter-node.spec.ts
│   ├── aggregate-node.spec.ts
│   └── join-node.spec.ts
├── workflows/
│   └── multi-node-workflow.spec.ts
└── edge-cases/
    ├── null-handling.spec.ts
    └── special-chars.spec.ts
```

### Page Object Example

```typescript
// pages/WorkflowCanvas.ts
import { Page, expect } from '@playwright/test';

export class WorkflowCanvas {
  constructor(private page: Page) {}

  async goto() {
    await this.page.goto('/');
  }

  async addNode(type: string, label: string) {
    await this.page.dragAndDrop(
      `[data-testid="node-palette-${type}"]`,
      '[data-testid="workflow-canvas"]'
    );
  }

  async uploadCSV(filePath: string) {
    const fileInput = this.page.locator('input[type="file"]');
    await fileInput.setInputFiles(filePath);
  }

  async runWorkflow() {
    await this.page.click('[data-testid="run-workflow-button"]');
  }

  async waitForResults() {
    await this.page.waitForSelector('[data-testid="data-preview-table"]');
  }

  async getRowCount() {
    const rows = await this.page.locator('[data-testid="data-preview-table"] tbody tr').count();
    return rows;
  }
}
```

### Test Example

```typescript
// nodes/filter-node.spec.ts
import { test, expect } from '@playwright/test';
import { WorkflowCanvas } from '../pages/WorkflowCanvas';

test.describe('Filter Node', () => {
  test('filters rows by single condition', async ({ page }) => {
    const canvas = new WorkflowCanvas(page);

    await canvas.goto();
    await canvas.uploadCSV('data/test_data_diverse.csv');
    await canvas.addNode('filter', 'Amount > 1000');
    await canvas.runWorkflow();
    await canvas.waitForResults();

    const rowCount = await canvas.getRowCount();
    expect(rowCount).toBeGreaterThan(0);
  });
});
```

## Best Practices

### 1. Use data-testid attributes
```typescript
// Good
await page.click('[data-testid="run-button"]');

// Avoid
await page.click('button:text("Run")');
```

### 2. Wait for elements explicitly
```typescript
// Good
await page.waitForSelector('[data-testid="results"]');
await expect(page.locator('[data-testid="results"]')).toBeVisible();

// Avoid
await page.waitForTimeout(5000);
```

### 3. Use proper assertions
```typescript
// Good
await expect(page.locator('[data-testid="row-count"]')).toHaveText('100');

// Avoid
const text = await page.locator('[data-testid="row-count"]').textContent();
expect(text).toBe('100');
```

### 4. Handle async operations
```typescript
// Good
await Promise.all([
  page.waitForNavigation(),
  page.click('[data-testid="submit"]')
]);

// Avoid
await page.click('[data-testid="submit"]');
await page.waitForNavigation();
```

## CI/CD Integration

### GitHub Actions
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

## Debugging

### Debug Mode
```bash
npx playwright test --debug
```

### Inspect Selectors
```bash
npx playwright codegen http://localhost:3000
```

### View Trace
```bash
npx playwright show-trace test-results/trace.zip
```
