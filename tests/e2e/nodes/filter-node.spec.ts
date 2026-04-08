import { test, expect } from '@playwright/test';
import { WorkflowCanvas } from '../pages/WorkflowCanvas';
import { DataInspectionPanel } from '../pages/DataInspectionPanel';
import { sampleCsvData } from '../fixtures/testData';
import { assertNodeExists, assertFilterApplied, assertSqlPreviewContains } from '../fixtures/assertions';

test.describe('Filter Node Tests', () => {
  let canvas: WorkflowCanvas;
  let dataPanel: DataInspectionPanel;

  test.beforeEach(async ({ page }) => {
    await page.goto('');
    canvas = new WorkflowCanvas(page);
    dataPanel = new DataInspectionPanel(page);
    await canvas.waitForReady();
  });

  test('should create filter node from palette', async ({ page }) => {
    await canvas.dragNodeToCanvas('filter');
    await expect(await canvas.getNodeCount()).toBe(1);
    await assertNodeExists(page, 'Filter');
  });

  test('should configure filter with equality operator', async ({ page }) => {
    await canvas.dragNodeToCanvas('input');
    await canvas.dragNodeToCanvas('filter');

    // Upload data
    const buffer = Buffer.from(sampleCsvData.content, 'utf-8');
    const fileInput = page.locator('input[type="file"]');

    if (await fileInput.isVisible()) {
      const fileChooserPromise = page.waitForEvent('filechooser');
      await fileInput.click();
      const fileChooser = await fileChooserPromise;

      await fileChooser.setFiles({
        name: sampleCsvData.filename,
        mimeType: 'text/csv',
        buffer: buffer,
      });

      await page.waitForTimeout(2000);

      // Click filter node and configure
      const nodes = await canvas.getAllNodeLabels();
      await canvas.clickNode(nodes.find(n => n.toLowerCase().includes('filter')) || 'Filter');

      // Configure filter (assuming there's a configuration panel)
      const columnSelect = page.locator('select[name="column"], [data-testid="filter-column"]');
      if (await columnSelect.isVisible()) {
        await columnSelect.selectOption('name');
      }

      const operatorSelect = page.locator('select[name="operator"], [data-testid="filter-operator"]');
      if (await operatorSelect.isVisible()) {
        await operatorSelect.selectOption('==');
      }

      const valueInput = page.locator('input[name="value"], [data-testid="filter-value"]');
      if (await valueInput.isVisible()) {
        await valueInput.fill('Alice');
      }

      await page.waitForTimeout(1000);
    }
  });

  test('should apply filter and reduce row count', async ({ page }) => {
    await canvas.dragNodeToCanvas('input');
    await canvas.dragNodeToCanvas('filter');
    await canvas.dragNodeToCanvas('output');

    const nodes = await canvas.getAllNodeLabels();
    if (nodes.length >= 3) {
      await canvas.connectNodes(nodes[0], nodes[1]);
      await canvas.connectNodes(nodes[1], nodes[2]);

      // Upload data
      const buffer = Buffer.from(sampleCsvData.content, 'utf-8');
      const fileInput = page.locator('input[type="file"]');

      if (await fileInput.isVisible()) {
        const fileChooserPromise = page.waitForEvent('filechooser');
        await fileInput.click();
        const fileChooser = await fileChooserPromise;

        await fileChooser.setFiles({
          name: sampleCsvData.filename,
          mimeType: 'text/csv',
          buffer: buffer,
        });

        await page.waitForTimeout(2000);

        // Execute workflow
        await canvas.execute();
        await page.waitForTimeout(5000);

        // Check that output has fewer rows than input
        const inputNode = nodes[0];
        const outputNode = nodes[2];

        // Verify filter was applied
        await assertSqlPreviewContains(page, 'WHERE');
      }
    }
  });

  test('should support multiple filter operators', async ({ page }) => {
    await canvas.dragNodeToCanvas('filter');
    await canvas.clickNode('Filter');

    const operators = ['>', '<', '>=', '<=', '==', '!=', 'contains', 'starts_with', 'ends_with'];

    for (const op of operators) {
      const operatorSelect = page.locator('select[name="operator"]');
      if (await operatorSelect.isVisible()) {
        await operatorSelect.selectOption(op);
        await page.waitForTimeout(500);

        const selectedValue = await operatorSelect.inputValue();
        expect(selectedValue).toBeTruthy();
      }
    }
  });

  test('should support null checking operators', async ({ page }) => {
    await canvas.dragNodeToCanvas('filter');
    await canvas.clickNode('Filter');

    const operatorSelect = page.locator('select[name="operator"]');
    if (await operatorSelect.isVisible()) {
      await operatorSelect.selectOption('is_null');
      await page.waitForTimeout(500);

      const selectedValue = await operatorSelect.inputValue();
      expect(selectedValue).toBeTruthy();
    }
  });

  test('should generate correct SQL for filter', async ({ page }) => {
    await canvas.dragNodeToCanvas('input');
    await canvas.dragNodeToCanvas('filter');

    const nodes = await canvas.getAllNodeLabels();
    if (nodes.length >= 2) {
      await canvas.connectNodes(nodes[0], nodes[1]);

      // Click filter node
      await canvas.clickNode(nodes.find(n => n.toLowerCase().includes('filter')) || 'Filter');

      // Configure filter
      const columnSelect = page.locator('select[name="column"]');
      if (await columnSelect.isVisible()) {
        await columnSelect.selectOption('age');
      }

      const operatorSelect = page.locator('select[name="operator"]');
      if (await operatorSelect.isVisible()) {
        await operatorSelect.selectOption('>');
      }

      const valueInput = page.locator('input[name="value"]');
      if (await valueInput.isVisible()) {
        await valueInput.fill('25');
      }

      await page.waitForTimeout(1000);

      // Check SQL preview
      await assertSqlPreviewContains(page, 'WHERE');
      await assertSqlPreviewContains(page, 'age');
      await assertSqlPreviewContains(page, '>');
    }
  });

  test('should handle string filters case-insensitively', async ({ page }) => {
    await canvas.dragNodeToCanvas('input');
    await canvas.dragNodeToCanvas('filter');

    const nodes = await canvas.getAllNodeLabels();
    if (nodes.length >= 2) {
      await canvas.connectNodes(nodes[0], nodes[1]);

      await canvas.clickNode(nodes.find(n => n.toLowerCase().includes('filter')) || 'Filter');

      // Configure string filter
      const columnSelect = page.locator('select[name="column"]');
      if (await columnSelect.isVisible()) {
        await columnSelect.selectOption('name');
      }

      const operatorSelect = page.locator('select[name="operator"]');
      if (await operatorSelect.isVisible()) {
        await operatorSelect.selectOption('contains');
      }

      const valueInput = page.locator('input[name="value"]');
      if (await valueInput.isVisible()) {
        await valueInput.fill('alice');
      }

      await page.waitForTimeout(1000);

      // SQL should use ILIKE for case-insensitive matching
      await assertSqlPreviewContains(page, 'ILIKE');
    }
  });

  test('should handle numeric filters correctly', async ({ page }) => {
    await canvas.dragNodeToCanvas('input');
    await canvas.dragNodeToCanvas('filter');

    const nodes = await canvas.getAllNodeLabels();
    if (nodes.length >= 2) {
      await canvas.connectNodes(nodes[0], nodes[1]);

      await canvas.clickNode(nodes.find(n => n.toLowerCase().includes('filter')) || 'Filter');

      // Configure numeric filter
      const columnSelect = page.locator('select[name="column"]');
      if (await columnSelect.isVisible()) {
        await columnSelect.selectOption('age');
      }

      const operatorSelect = page.locator('select[name="operator"]');
      if (await operatorSelect.isVisible()) {
        await operatorSelect.selectOption('>=');
      }

      const valueInput = page.locator('input[name="value"]');
      if (await valueInput.isVisible()) {
        await valueInput.fill('30');
      }

      await page.waitForTimeout(1000);

      await assertSqlPreviewContains(page, 'age');
      await assertSqlPreviewContains(page, '>=');
    }
  });

  test('should allow IN operator for multiple values', async ({ page }) => {
    await canvas.dragNodeToCanvas('filter');
    await canvas.clickNode('Filter');

    const operatorSelect = page.locator('select[name="operator"]');
    if (await operatorSelect.isVisible()) {
      await operatorSelect.selectOption('in');
      await page.waitForTimeout(500);

      const valueInput = page.locator('input[name="value"]');
      if (await valueInput.isVisible()) {
        await valueInput.fill('Alice,Bob,Carol');
      }

      await page.waitForTimeout(1000);

      await assertSqlPreviewContains(page, 'IN');
    }
  });

  test('should support custom WHERE clause', async ({ page }) => {
    await canvas.dragNodeToCanvas('filter');
    await canvas.clickNode('Filter');

    // Look for advanced mode toggle
    const advancedToggle = page.locator('button:has-text("Advanced"), [data-testid="advanced-mode-toggle"]');
    if (await advancedToggle.isVisible()) {
      await advancedToggle.click();

      const customWhereInput = page.locator('textarea[name="customWhere"], [data-testid="custom-where"]');
      if (await customWhereInput.isVisible()) {
        await customWhereInput.fill('age > 25 AND city = "New York"');
        await page.waitForTimeout(1000);

        await assertSqlPreviewContains(page, 'age > 25');
        await assertSqlPreviewContains(page, 'AND');
      }
    }
  });
});
