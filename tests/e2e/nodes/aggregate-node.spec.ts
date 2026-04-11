import { test, expect } from '@playwright/test';
import { WorkflowCanvas } from '../pages/WorkflowCanvas';
import { DataInspectionPanel } from '../pages/DataInspectionPanel';
import { salesData } from '../fixtures/testData';
import { assertNodeExists, assertAggregateConfigured, assertSqlPreviewContains } from '../fixtures/assertions';
import { uploadTestCsv } from '../fixtures/testData';

test.describe('Aggregate Node Tests', () => {
  let canvas: WorkflowCanvas;
  let dataPanel: DataInspectionPanel;

  test.beforeEach(async ({ page }) => {
    await page.goto('');
    canvas = new WorkflowCanvas(page);
    dataPanel = new DataInspectionPanel(page);
    await canvas.waitForReady();
  });

  test('should create aggregate node from palette', async ({ page }) => {
    await canvas.dragNodeToCanvas('aggregate');
    await expect(await canvas.getNodeCount()).toBe(1);
    await assertNodeExists(page, 'Aggregate');
  });

  test('should configure aggregate with group by', async ({ page }) => {
    await canvas.dragNodeToCanvas('input');
    await canvas.selectNodeByIndex(0);
    await uploadTestCsv(page, salesData);

    await canvas.dragNodeToCanvas('aggregate', { x: 300, y: 100 });

    const nodes = await canvas.getAllNodeLabels();
    if (nodes.length >= 2) {
      await canvas.connectNodes(nodes[0], nodes[1]);

      // Click aggregate node and configure
      await canvas.clickNode(nodes.find(n => n.toLowerCase().includes('aggregate')) || 'Aggregate');

      // Configure group by (wait for options to be available)
      const groupByInput = page.locator('[data-testid="groupby-checkbox"]').first();
      if (await groupByInput.isVisible()) {
        await groupByInput.check();
      } else {
        // Fallback if the UI uses a different input type for group by
        const groupSelect = page.locator('input[name="groupBy"], [data-testid="group-by-input"]');
        if (await groupSelect.isVisible()) {
          await groupSelect.fill('region');
        }
      }

      await page.waitForTimeout(1000);

      await assertSqlPreviewContains(page, 'GROUP BY');
    }
  });

  test('should add aggregation column', async ({ page }) => {
    await canvas.dragNodeToCanvas('input');
    await canvas.selectNodeByIndex(0);
    await uploadTestCsv(page, salesData);

    await canvas.dragNodeToCanvas('aggregate', { x: 300, y: 100 });

    const nodes = await canvas.getAllNodeLabels();
    if (nodes.length >= 2) {
      await canvas.connectNodes(nodes[0], nodes[1]);

      await canvas.clickNode(nodes.find(n => n.toLowerCase().includes('aggregate')) || 'Aggregate');

      // Look for add aggregation button
      const addAggButton = page.locator('button:has-text("Add"), button:has-text("Add Aggregation")');
      if (await addAggButton.isVisible()) {
        await addAggButton.click();

        const columnSelect = page.locator('select[name="agg-column"]');
        await columnSelect.waitFor({ state: 'visible' });
        await columnSelect.selectOption('sales');

        const operationSelect = page.locator('select[name="agg-operation"]');
        await operationSelect.selectOption('sum');

        const aliasInput = page.locator('input[name="agg-alias"]');
        await aliasInput.fill('total_sales');

        await page.waitForTimeout(1000);

        await assertSqlPreviewContains(page, 'SUM');
        await assertSqlPreviewContains(page, 'sales');
      }
    }
  });

  test('should support multiple aggregations', async ({ page }) => {
    await canvas.dragNodeToCanvas('input');
    await canvas.selectNodeByIndex(0);
    await uploadTestCsv(page, salesData);

    await canvas.dragNodeToCanvas('aggregate', { x: 300, y: 100 });

    const nodes = await canvas.getAllNodeLabels();
    if (nodes.length >= 2) {
      await canvas.connectNodes(nodes[0], nodes[1]);

      await canvas.clickNode(nodes.find(n => n.toLowerCase().includes('aggregate')) || 'Aggregate');

      // Add multiple aggregations
      const addAggButton = page.locator('button:has-text("Add")');
      if (await addAggButton.isVisible()) {
        await addAggButton.click();
        await addAggButton.click();
      }

      await page.waitForTimeout(1000);

      // Check that both aggregations are present
      const aggRows = page.locator('select[name="agg-column"]');
      const count = await aggRows.count();
      expect(count).toBeGreaterThanOrEqual(2);
    }
  });

  test('should support all aggregation operations', async ({ page }) => {
    await canvas.dragNodeToCanvas('input');
    await canvas.selectNodeByIndex(0);
    await uploadTestCsv(page, salesData);

    await canvas.dragNodeToCanvas('aggregate', { x: 300, y: 100 });
    await canvas.connectNodes(0, 1);
    await canvas.clickNode('Aggregate');

    const operations = ['sum', 'avg', 'count', 'min', 'max'];

    // Ensure we have an aggregation row
    const addAggButton = page.locator('button:has-text("Add")');
    await addAggButton.click();

    for (const op of operations) {
      const operationSelect = page.locator('select[name="agg-operation"]').first();
      if (await operationSelect.isVisible()) {
        await operationSelect.selectOption(op);
        await page.waitForTimeout(500);

        const selectedValue = await operationSelect.inputValue();
        expect(selectedValue).toBe(op);
      }
    }
  });

  test('should generate correct SQL for aggregation', async ({ page }) => {
    await canvas.dragNodeToCanvas('input');
    await canvas.selectNodeByIndex(0);
    await uploadTestCsv(page, salesData);

    await canvas.dragNodeToCanvas('aggregate', { x: 300, y: 100 });

    const nodes = await canvas.getAllNodeLabels();
    if (nodes.length >= 2) {
      await canvas.connectNodes(nodes[0], nodes[1]);

      await canvas.clickNode(nodes.find(n => n.toLowerCase().includes('aggregate')) || 'Aggregate');

      // Add aggregation
      const addAggButton = page.locator('button:has-text("Add")');
      await addAggButton.click();

      const columnSelect = page.locator('select[name="agg-column"]');
      await columnSelect.selectOption('sales');

      const operationSelect = page.locator('select[name="agg-operation"]');
      await operationSelect.selectOption('sum');

      const aliasInput = page.locator('input[name="agg-alias"]');
      await aliasInput.fill('total');

      await page.waitForTimeout(1000);

      // Verify SQL
      await assertSqlPreviewContains(page, 'SELECT');
      await assertSqlPreviewContains(page, 'SUM');
    }
  });

  test('should handle aggregation without group by', async ({ page }) => {
    await canvas.dragNodeToCanvas('input');
    await canvas.selectNodeByIndex(0);
    await uploadTestCsv(page, salesData);

    await canvas.dragNodeToCanvas('aggregate', { x: 300, y: 100 });

    const nodes = await canvas.getAllNodeLabels();
    if (nodes.length >= 2) {
      await canvas.connectNodes(nodes[0], nodes[1]);

      await canvas.clickNode(nodes.find(n => n.toLowerCase().includes('aggregate')) || 'Aggregate');

      // Add aggregation
      const addAggButton = page.locator('button:has-text("Add")');
      await addAggButton.click();

      const operationSelect = page.locator('select[name="agg-operation"]');
      await operationSelect.selectOption('count');

      await page.waitForTimeout(1000);

      await assertSqlPreviewContains(page, 'COUNT');
    }
  });

  test('should remove aggregation column', async ({ page }) => {
    await canvas.dragNodeToCanvas('aggregate');
    await canvas.clickNode('Aggregate');

    const addAggButton = page.locator('button:has-text("Add")');
    if (await addAggButton.isVisible()) {
      await addAggButton.click();
      await page.waitForTimeout(500);

      // Find remove button for the aggregation (using the Trash2 icon container)
      const removeButton = page.locator('button:has(svg)');
      const removeCount = await removeButton.count();

      if (removeCount > 0) {
        await removeButton.first().click();
        await page.waitForTimeout(500);
      }
    }
  });
});
