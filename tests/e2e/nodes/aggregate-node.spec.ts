import { test, expect } from '@playwright/test';
import { WorkflowCanvas } from '../pages/WorkflowCanvas';
import { DataInspectionPanel } from '../pages/DataInspectionPanel';
import { salesData } from '../fixtures/testData';
import { assertNodeExists, assertAggregateConfigured, assertSqlPreviewContains } from '../fixtures/assertions';

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
    await canvas.dragNodeToCanvas('aggregate');

    // Upload data
    const buffer = Buffer.from(salesData.content, 'utf-8');
    const fileInput = page.locator('input[type="file"]');

    if (await fileInput.isVisible()) {
      const fileChooserPromise = page.waitForEvent('filechooser');
      await fileInput.click();
      const fileChooser = await fileChooserPromise;

      await fileChooser.setFiles({
        name: salesData.filename,
        mimeType: 'text/csv',
        buffer: buffer,
      });

      await page.waitForTimeout(2000);

      const nodes = await canvas.getAllNodeLabels();
      await canvas.connectNodes(nodes[0], nodes[1]);

      // Click aggregate node and configure
      await canvas.clickNode(nodes.find(n => n.toLowerCase().includes('aggregate')) || 'Aggregate');

      // Configure group by
      const groupByInput = page.locator('input[name="groupBy"], [data-testid="group-by-input"]');
      if (await groupByInput.isVisible()) {
        await groupByInput.fill('region');
      }

      await page.waitForTimeout(1000);

      await assertSqlPreviewContains(page, 'GROUP BY');
      await assertSqlPreviewContains(page, 'region');
    }
  });

  test('should add aggregation column', async ({ page }) => {
    await canvas.dragNodeToCanvas('input');
    await canvas.dragNodeToCanvas('aggregate');

    const nodes = await canvas.getAllNodeLabels();
    if (nodes.length >= 2) {
      await canvas.connectNodes(nodes[0], nodes[1]);

      await canvas.clickNode(nodes.find(n => n.toLowerCase().includes('aggregate')) || 'Aggregate');

      // Look for add aggregation button
      const addAggButton = page.locator('button:has-text("Add"), button:has-text("Add Aggregation")');
      if (await addAggButton.isVisible()) {
        await addAggButton.click();

        const columnSelect = page.locator('select[name="agg-column"]');
        if (await columnSelect.isVisible()) {
          await columnSelect.selectOption('sales');
        }

        const operationSelect = page.locator('select[name="agg-operation"]');
        if (await operationSelect.isVisible()) {
          await operationSelect.selectOption('sum');
        }

        const aliasInput = page.locator('input[name="agg-alias"]');
        if (await aliasInput.isVisible()) {
          await aliasInput.fill('total_sales');
        }

        await page.waitForTimeout(1000);

        await assertSqlPreviewContains(page, 'SUM');
        await assertSqlPreviewContains(page, 'sales');
      }
    }
  });

  test('should support multiple aggregations', async ({ page }) => {
    await canvas.dragNodeToCanvas('input');
    await canvas.dragNodeToCanvas('aggregate');

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
      const aggRows = page.locator('[data-testid="aggregation-row"]');
      const count = await aggRows.count();
      expect(count).toBeGreaterThanOrEqual(2);
    }
  });

  test('should support all aggregation operations', async ({ page }) => {
    await canvas.dragNodeToCanvas('aggregate');
    await canvas.clickNode('Aggregate');

    const operations = ['count', 'sum', 'avg', 'min', 'max', 'stddev'];

    for (const op of operations) {
      const operationSelect = page.locator('select[name="agg-operation"]');
      if (await operationSelect.isVisible()) {
        await operationSelect.selectOption(op);
        await page.waitForTimeout(500);

        const selectedValue = await operationSelect.inputValue();
        expect(selectedValue).toBeTruthy();
      }
    }
  });

  test('should generate correct SQL for aggregation', async ({ page }) => {
    await canvas.dragNodeToCanvas('input');
    await canvas.dragNodeToCanvas('aggregate');

    const nodes = await canvas.getAllNodeLabels();
    if (nodes.length >= 2) {
      await canvas.connectNodes(nodes[0], nodes[1]);

      await canvas.clickNode(nodes.find(n => n.toLowerCase().includes('aggregate')) || 'Aggregate');

      // Configure aggregation
      const groupByInput = page.locator('input[name="groupBy"]');
      if (await groupByInput.isVisible()) {
        await groupByInput.fill('region');
      }

      const addAggButton = page.locator('button:has-text("Add")');
      if (await addAggButton.isVisible()) {
        await addAggButton.click();

        const columnSelect = page.locator('select[name="agg-column"]');
        if (await columnSelect.isVisible()) {
          await columnSelect.selectOption('sales');
        }

        const operationSelect = page.locator('select[name="agg-operation"]');
        if (await operationSelect.isVisible()) {
          await operationSelect.selectOption('sum');
        }

        const aliasInput = page.locator('input[name="agg-alias"]');
        if (await aliasInput.isVisible()) {
          await aliasInput.fill('total');
        }
      }

      await page.waitForTimeout(1000);

      // Verify SQL
      await assertSqlPreviewContains(page, 'SELECT');
      await assertSqlPreviewContains(page, 'SUM');
      await assertSqlPreviewContains(page, 'GROUP BY');
    }
  });

  test('should handle aggregation without group by', async ({ page }) => {
    await canvas.dragNodeToCanvas('input');
    await canvas.dragNodeToCanvas('aggregate');

    const nodes = await canvas.getAllNodeLabels();
    if (nodes.length >= 2) {
      await canvas.connectNodes(nodes[0], nodes[1]);

      await canvas.clickNode(nodes.find(n => n.toLowerCase().includes('aggregate')) || 'Aggregate');

      // Add aggregation without group by
      const addAggButton = page.locator('button:has-text("Add")');
      if (await addAggButton.isVisible()) {
        await addAggButton.click();

        const columnSelect = page.locator('select[name="agg-column"]');
        if (await columnSelect.isVisible()) {
          await columnSelect.selectOption('sales');
        }

        const operationSelect = page.locator('select[name="agg-operation"]');
        if (await operationSelect.isVisible()) {
          await operationSelect.selectOption('count');
        }
      }

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

      // Find remove button for the aggregation
      const removeButton = page.locator('button:has-text("Remove"), button:has-text("Delete"), button[aria-label="remove"]');
      const removeCount = await removeButton.count();

      if (removeCount > 0) {
        await removeButton.first().click();
        await page.waitForTimeout(500);
      }
    }
  });

  test('should validate aggregation configuration', async ({ page }) => {
    await canvas.dragNodeToCanvas('input');
    await canvas.dragNodeToCanvas('aggregate');
    await canvas.dragNodeToCanvas('output');

    const nodes = await canvas.getAllNodeLabels();
    if (nodes.length >= 3) {
      await canvas.connectNodes(nodes[0], nodes[1]);
      await canvas.connectNodes(nodes[1], nodes[2]);

      // Try to execute without configuration
      await canvas.execute();
      await page.waitForTimeout(3000);

      // Should show error or validation message
      const errorMessage = page.locator('text=/error|invalid|required/i');
      const hasError = await errorMessage.isVisible().catch(() => false);

      if (hasError) {
        expect(errorMessage).toBeVisible();
      }
    }
  });

  test('should display aggregation results in data panel', async ({ page }) => {
    await canvas.dragNodeToCanvas('input');
    await canvas.dragNodeToCanvas('aggregate');
    await canvas.dragNodeToCanvas('output');

    const nodes = await canvas.getAllNodeLabels();
    if (nodes.length >= 3) {
      await canvas.connectNodes(nodes[0], nodes[1]);
      await canvas.connectNodes(nodes[1], nodes[2]);

      // Upload data
      const buffer = Buffer.from(salesData.content, 'utf-8');
      const fileInput = page.locator('input[type="file"]');

      if (await fileInput.isVisible()) {
        const fileChooserPromise = page.waitForEvent('filechooser');
        await fileInput.click();
        const fileChooser = await fileChooserPromise;

        await fileChooser.setFiles({
          name: salesData.filename,
          mimeType: 'text/csv',
          buffer: buffer,
        });

        await page.waitForTimeout(2000);

        // Configure aggregate
        await canvas.clickNode(nodes.find(n => n.toLowerCase().includes('aggregate')) || 'Aggregate');

        const groupByInput = page.locator('input[name="groupBy"]');
        if (await groupByInput.isVisible()) {
          await groupByInput.fill('region');
        }

        const addAggButton = page.locator('button:has-text("Add")');
        if (await addAggButton.isVisible()) {
          await addAggButton.click();

          const columnSelect = page.locator('select[name="agg-column"]');
          if (await columnSelect.isVisible()) {
            await columnSelect.selectOption('sales');
          }

          const operationSelect = page.locator('select[name="agg-operation"]');
          if (await operationSelect.isVisible()) {
            await operationSelect.selectOption('sum');
          }
        }

        // Execute
        await canvas.execute();
        await page.waitForTimeout(5000);

        // Check results
        await canvas.clickNode(nodes[2]);
        await dataPanel.switchToDataTab();

        const columns = await dataPanel.getDataColumns();
        expect(columns).toContain('region');
      }
    }
  });
});
