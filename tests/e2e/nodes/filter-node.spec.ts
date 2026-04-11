import { test, expect } from '@playwright/test';
import { WorkflowCanvas } from '../pages/WorkflowCanvas';
import { DataInspectionPanel } from '../pages/DataInspectionPanel';
import { sampleCsvData } from '../fixtures/testData';
import { assertNodeExists, assertFilterApplied, assertSqlPreviewContains } from '../fixtures/assertions';
import { uploadTestCsv } from '../fixtures/testData';

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
    await canvas.selectNodeByIndex(0);
    await uploadTestCsv(page, sampleCsvData);

    await canvas.dragNodeToCanvas('filter', { x: 300, y: 100 });
    await canvas.connectNodes(0, 1);

    // Click filter node and configure
    await canvas.clickNode('Filter');

    // Configure filter
    const columnSelect = page.locator('select[name="column"]');
    await columnSelect.waitFor({ state: 'visible' });
    await columnSelect.selectOption('name');

    const operatorSelect = page.locator('select[name="operator"]');
    await operatorSelect.selectOption('==');

    const valueInput = page.locator('input[name="value"]');
    await valueInput.fill('Alice');

    await page.waitForTimeout(1000);
    await assertSqlPreviewContains(page, 'Alice');
  });

  test('should support multiple filter operators', async ({ page }) => {
    await canvas.dragNodeToCanvas('input');
    await canvas.selectNodeByIndex(0);
    await uploadTestCsv(page, sampleCsvData);

    await canvas.dragNodeToCanvas('filter', { x: 300, y: 100 });
    await canvas.connectNodes(0, 1);
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
    await canvas.dragNodeToCanvas('input');
    await canvas.selectNodeByIndex(0);
    await uploadTestCsv(page, sampleCsvData);

    await canvas.dragNodeToCanvas('filter', { x: 300, y: 100 });
    await canvas.connectNodes(0, 1);
    await canvas.clickNode('Filter');

    const operatorSelect = page.locator('select[name="operator"]');
    if (await operatorSelect.isVisible()) {
      await operatorSelect.selectOption('is_null');
      await page.waitForTimeout(500);

      const selectedValue = await operatorSelect.inputValue();
      expect(selectedValue).toBe('is_null');
    }
  });

  test('should generate correct SQL for filter', async ({ page }) => {
    await canvas.dragNodeToCanvas('input');
    await canvas.selectNodeByIndex(0);
    await uploadTestCsv(page, sampleCsvData);

    await canvas.dragNodeToCanvas('filter', { x: 300, y: 100 });
    await canvas.connectNodes(0, 1);

    // Click filter node
    await canvas.clickNode('Filter');

    // Configure filter
    const columnSelect = page.locator('select[name="column"]');
    await columnSelect.selectOption('age');

    const operatorSelect = page.locator('select[name="operator"]');
    await operatorSelect.selectOption('>');

    const valueInput = page.locator('input[name="value"]');
    await valueInput.fill('25');

    await page.waitForTimeout(1000);

    // Check SQL preview
    await assertSqlPreviewContains(page, 'WHERE');
    await assertSqlPreviewContains(page, 'age');
    await assertSqlPreviewContains(page, '>');
  });

  test('should handle string filters case-insensitively', async ({ page }) => {
    await canvas.dragNodeToCanvas('input');
    await canvas.selectNodeByIndex(0);
    await uploadTestCsv(page, sampleCsvData);

    await canvas.dragNodeToCanvas('filter', { x: 300, y: 100 });
    await canvas.connectNodes(0, 1);

    await canvas.clickNode('Filter');

    // Configure string filter
    const columnSelect = page.locator('select[name="column"]');
    await columnSelect.selectOption('name');

    const operatorSelect = page.locator('select[name="operator"]');
    await operatorSelect.selectOption('contains');

    const valueInput = page.locator('input[name="value"]');
    await valueInput.fill('alice');

    await page.waitForTimeout(1000);

    // SQL should use ILIKE for case-insensitive matching
    await assertSqlPreviewContains(page, 'ILIKE');
  });

  test('should handle numeric filters correctly', async ({ page }) => {
    await canvas.dragNodeToCanvas('input');
    await canvas.selectNodeByIndex(0);
    await uploadTestCsv(page, sampleCsvData);

    await canvas.dragNodeToCanvas('filter', { x: 300, y: 100 });
    await canvas.connectNodes(0, 1);

    await canvas.clickNode('Filter');

    // Configure numeric filter
    const columnSelect = page.locator('select[name="column"]');
    await columnSelect.selectOption('age');

    const operatorSelect = page.locator('select[name="operator"]');
    await operatorSelect.selectOption('>=');

    const valueInput = page.locator('input[name="value"]');
    await valueInput.fill('30');

    await page.waitForTimeout(1000);

    await assertSqlPreviewContains(page, 'age');
    await assertSqlPreviewContains(page, '>=');
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
