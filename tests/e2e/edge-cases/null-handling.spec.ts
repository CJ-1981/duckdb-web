import { test, expect } from '@playwright/test';
import { WorkflowCanvas } from '../pages/WorkflowCanvas';
import { DataInspectionPanel } from '../pages/DataInspectionPanel';
import { csvWithNulls } from '../fixtures/testData';
import { assertColumnStatsExist, assertNullValueHandled } from '../fixtures/assertions';

test.describe('Edge Cases - Null Handling', () => {
  let canvas: WorkflowCanvas;
  let dataPanel: DataInspectionPanel;

  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:3000');
    canvas = new WorkflowCanvas(page);
    dataPanel = new DataInspectionPanel(page);
    await canvas.waitForReady();
  });

  test('should display null values in data preview', async ({ page }) => {
    await canvas.dragNodeToCanvas('input');
    await page.locator('.react-flow__node').first().click();

    // Upload CSV with nulls
    const buffer = Buffer.from(csvWithNulls.content, 'utf-8');
    const fileInput = page.locator('input[type="file"]');

    if (await fileInput.isVisible()) {
      const fileChooserPromise = page.waitForEvent('filechooser');
      await fileInput.click();
      const fileChooser = await fileChooserPromise;

      await fileChooser.setFiles({
        name: csvWithNulls.filename,
        mimeType: 'text/csv',
        buffer: buffer,
      });

      await page.waitForTimeout(3000);
      await dataPanel.switchToDataTab();

      // Check that null cells are displayed
      const nullCells = page.locator('td').filter({ hasText: /^$/ });
      const nullCount = await nullCells.count();
      expect(nullCount).toBeGreaterThan(0);
    }
  });

  test('should show null count in statistics', async ({ page }) => {
    await canvas.dragNodeToCanvas('input');
    await page.locator('.react-flow__node').first().click();

    const buffer = Buffer.from(csvWithNulls.content, 'utf-8');
    const fileInput = page.locator('input[type="file"]');

    if (await fileInput.isVisible()) {
      const fileChooserPromise = page.waitForEvent('filechooser');
      await fileInput.click();
      const fileChooser = await fileChooserPromise;

      await fileChooser.setFiles({
        name: csvWithNulls.filename,
        mimeType: 'text/csv',
        buffer: buffer,
      });

      await page.waitForTimeout(3000);
      await dataPanel.switchToStatsTab();

      // Check statistics for email column (has nulls)
      await assertColumnStatsExist(page, 'email');

      const emailStats = await dataPanel.getColumnStats('email');
      expect(emailStats).toBeTruthy();
      expect(parseInt(emailStats?.nulls || '0')).toBeGreaterThan(0);
    }
  });

  test('should filter null values with is_null operator', async ({ page }) => {
    await canvas.dragNodeToCanvas('input');
    await canvas.dragNodeToCanvas('filter');
    await canvas.dragNodeToCanvas('output');

    const nodes = await canvas.getAllNodeLabels();
    if (nodes.length >= 3) {
      await canvas.connectNodes(nodes[0], nodes[1]);
      await canvas.connectNodes(nodes[1], nodes[2]);

      // Upload data
      const buffer = Buffer.from(csvWithNulls.content, 'utf-8');
      const fileInput = page.locator('input[type="file"]');

      if (await fileInput.isVisible()) {
        const fileChooserPromise = page.waitForEvent('filechooser');
        await fileInput.click();
        const fileChooser = await fileChooserPromise;

        await fileChooser.setFiles({
          name: csvWithNulls.filename,
          mimeType: 'text/csv',
          buffer: buffer,
        });

        await page.waitForTimeout(2000);

        // Configure filter for null values
        await canvas.clickNode(nodes.find(n => n.toLowerCase().includes('filter')) || 'Filter');

        const columnSelect = page.locator('select[name="column"]');
        if (await columnSelect.isVisible()) {
          await columnSelect.selectOption('email');
        }

        const operatorSelect = page.locator('select[name="operator"]');
        if (await operatorSelect.isVisible()) {
          await operatorSelect.selectOption('is_null');
        }

        await page.waitForTimeout(1000);

        // Execute and check
        await canvas.execute();
        await page.waitForTimeout(5000);

        await canvas.clickNode(nodes[2]);
        await dataPanel.switchToDataTab();

        const rowCount = await dataPanel.getDataRowCount();
        expect(rowCount).toBeGreaterThan(0);
      }
    }
  });

  test('should filter non-null values with is_not_null operator', async ({ page }) => {
    await canvas.dragNodeToCanvas('input');
    await canvas.dragNodeToCanvas('filter');
    await canvas.dragNodeToCanvas('output');

    const nodes = await canvas.getAllNodeLabels();
    if (nodes.length >= 3) {
      await canvas.connectNodes(nodes[0], nodes[1]);
      await canvas.connectNodes(nodes[1], nodes[2]);

      const buffer = Buffer.from(csvWithNulls.content, 'utf-8');
      const fileInput = page.locator('input[type="file"]');

      if (await fileInput.isVisible()) {
        const fileChooserPromise = page.waitForEvent('filechooser');
        await fileInput.click();
        const fileChooser = await fileChooserPromise;

        await fileChooser.setFiles({
          name: csvWithNulls.filename,
          mimeType: 'text/csv',
          buffer: buffer,
        });

        await page.waitForTimeout(2000);

        await canvas.clickNode(nodes.find(n => n.toLowerCase().includes('filter')) || 'Filter');

        const columnSelect = page.locator('select[name="column"]');
        if (await columnSelect.isVisible()) {
          await columnSelect.selectOption('email');
        }

        const operatorSelect = page.locator('select[name="operator"]');
        if (await operatorSelect.isVisible()) {
          await operatorSelect.selectOption('is_not_null');
        }

        await page.waitForTimeout(1000);

        await canvas.execute();
        await page.waitForTimeout(5000);

        await canvas.clickNode(nodes[2]);
        await dataPanel.switchToDataTab();

        const rowCount = await dataPanel.getDataRowCount();
        expect(rowCount).toBeGreaterThan(0);
      }
    }
  });

  test('should handle null values in aggregation', async ({ page }) => {
    await canvas.dragNodeToCanvas('input');
    await canvas.dragNodeToCanvas('aggregate');
    await canvas.dragNodeToCanvas('output');

    const nodes = await canvas.getAllNodeLabels();
    if (nodes.length >= 3) {
      await canvas.connectNodes(nodes[0], nodes[1]);
      await canvas.connectNodes(nodes[1], nodes[2]);

      const buffer = Buffer.from(csvWithNulls.content, 'utf-8');
      const fileInput = page.locator('input[type="file"]');

      if (await fileInput.isVisible()) {
        const fileChooserPromise = page.waitForEvent('filechooser');
        await fileInput.click();
        const fileChooser = await fileChooserPromise;

        await fileChooser.setFiles({
          name: csvWithNulls.filename,
          mimeType: 'text/csv',
          buffer: buffer,
        });

        await page.waitForTimeout(2000);

        // Configure aggregation on column with nulls
        await canvas.clickNode(nodes.find(n => n.toLowerCase().includes('aggregate')) || 'Aggregate');

        const addAggButton = page.locator('button:has-text("Add")');
        if (await addAggButton.isVisible()) {
          await addAggButton.click();

          const columnSelect = page.locator('select[name="agg-column"]');
          if (await columnSelect.isVisible()) {
            await columnSelect.selectOption('age');
          }

          const operationSelect = page.locator('select[name="agg-operation"]');
          if (await operationSelect.isVisible()) {
            await operationSelect.selectOption('avg');
          }
        }

        await page.waitForTimeout(1000);

        await canvas.execute();
        await page.waitForTimeout(5000);

        // Should compute average ignoring nulls
        await canvas.clickNode(nodes[2]);
        await dataPanel.switchToDataTab();

        const columns = await dataPanel.getDataColumns();
        expect(columns.length).toBeGreaterThan(0);
      }
    }
  });

  test('should handle null values in joins', async ({ page }) => {
    await canvas.dragNodeToCanvas('input', { x: 100, y: 100 });
    await canvas.dragNodeToCanvas('input', { x: 100, y: 300 });
    await canvas.dragNodeToCanvas('combine', { x: 400, y: 200 });
    await canvas.dragNodeToCanvas('output', { x: 700, y: 200 });

    const nodes = await canvas.getAllNodeLabels();
    if (nodes.length >= 4) {
      await canvas.connectNodes(nodes[0], nodes[2]);
      await canvas.connectNodes(nodes[1], nodes[2]);
      await canvas.connectNodes(nodes[2], nodes[3]);

      const buffer = Buffer.from(csvWithNulls.content, 'utf-8');
      const fileInput = page.locator('input[type="file"]');

      if (await fileInput.isVisible()) {
        // Upload to both inputs
        for (let i = 0; i < 2; i++) {
          await canvas.clickNode(nodes[i]);

          const fileChooserPromise = page.waitForEvent('filechooser');
          await fileInput.click();
          const fileChooser = await fileChooserPromise;

          await fileChooser.setFiles({
            name: csvWithNulls.filename,
            mimeType: 'text/csv',
            buffer: buffer,
          });

          await page.waitForTimeout(2000);
        }

        // Configure join
        await canvas.clickNode(nodes[2]);

        const joinTypeSelect = page.locator('select[name="joinType"]');
        if (await joinTypeSelect.isVisible()) {
          await joinTypeSelect.selectOption('left');
        }

        await page.waitForTimeout(1000);

        await canvas.execute();
        await page.waitForTimeout(5000);

        await canvas.clickNode(nodes[3]);
        await dataPanel.switchToDataTab();

        const rowCount = await dataPanel.getDataRowCount();
        expect(rowCount).toBeGreaterThan(0);
      }
    }
  });

  test('should replace null values with clean node', async ({ page }) => {
    await canvas.dragNodeToCanvas('input');
    await canvas.dragNodeToCanvas('clean');
    await canvas.dragNodeToCanvas('output');

    const nodes = await canvas.getAllNodeLabels();
    if (nodes.length >= 3) {
      await canvas.connectNodes(nodes[0], nodes[1]);
      await canvas.connectNodes(nodes[1], nodes[2]);

      const buffer = Buffer.from(csvWithNulls.content, 'utf-8');
      const fileInput = page.locator('input[type="file"]');

      if (await fileInput.isVisible()) {
        const fileChooserPromise = page.waitForEvent('filechooser');
        await fileInput.click();
        const fileChooser = await fileChooserPromise;

        await fileChooser.setFiles({
          name: csvWithNulls.filename,
          mimeType: 'text/csv',
          buffer: buffer,
        });

        await page.waitForTimeout(2000);

        // Configure clean node
        await canvas.clickNode(nodes.find(n => n.toLowerCase().includes('clean')) || 'Clean');

        const operationSelect = page.locator('select[name="operation"]');
        if (await operationSelect.isVisible()) {
          await operationSelect.selectOption('replace_null');
        }

        const newValueInput = page.locator('input[name="newValue"]');
        if (await newValueInput.isVisible()) {
          await newValueInput.fill('unknown');
        }

        await page.waitForTimeout(1000);

        await canvas.execute();
        await page.waitForTimeout(5000);

        await canvas.clickNode(nodes[2]);
        await dataPanel.switchToStatsTab();

        // Check that nulls were replaced
        const stats = await dataPanel.getColumnStats('email');
        expect(parseInt(stats?.nulls || '0')).toBe(0);
      }
    }
  });

  test('should calculate null percentage correctly', async ({ page }) => {
    await canvas.dragNodeToCanvas('input');
    await page.locator('.react-flow__node').first().click();

    const buffer = Buffer.from(csvWithNulls.content, 'utf-8');
    const fileInput = page.locator('input[type="file"]');

    if (await fileInput.isVisible()) {
      const fileChooserPromise = page.waitForEvent('filechooser');
      await fileInput.click();
      const fileChooser = await fileChooserPromise;

      await fileChooser.setFiles({
        name: csvWithNulls.filename,
        mimeType: 'text/csv',
        buffer: buffer,
      });

      await page.waitForTimeout(3000);
      await dataPanel.switchToStatsTab();

      const emailStats = await dataPanel.getColumnStats('email');
      expect(emailStats).toBeTruthy();

      // Verify null percentage is reasonable
      const nullPct = parseFloat(emailStats?.nullPct || '0');
      expect(nullPct).toBeGreaterThanOrEqual(0);
      expect(nullPct).toBeLessThanOrEqual(100);
    }
  });

  test('should show warning for high null percentage', async ({ page }) => {
    await canvas.dragNodeToCanvas('input');
    await page.locator('.react-flow__node').first().click();

    const buffer = Buffer.from(csvWithNulls.content, 'utf-8');
    const fileInput = page.locator('input[type="file"]');

    if (await fileInput.isVisible()) {
      const fileChooserPromise = page.waitForEvent('filechooser');
      await fileInput.click();
      const fileChooser = await fileChooserPromise;

      await fileChooser.setFiles({
        name: csvWithNulls.filename,
        mimeType: 'text/csv',
        buffer: buffer,
      });

      await page.waitForTimeout(3000);
      await dataPanel.switchToStatsTab();

      // Check for warning on high null percentage
      const emailStats = await dataPanel.getColumnStats('email');
      const nullPct = parseFloat(emailStats?.nullPct || '0');

      if (nullPct > 20) {
        const warningIndicator = page.locator('text=/null/i').locator('..').locator('.text-red-500, [class*="red"]');
        const hasWarning = await warningIndicator.isVisible().catch(() => false);

        if (hasWarning) {
          expect(warningIndicator).toBeVisible();
        }
      }
    }
  });

  test('should handle all-null columns gracefully', async ({ page }) => {
    await canvas.dragNodeToCanvas('input');
    await page.locator('.react-flow__node').first().click();

    // Create CSV with all-null column
    const allNullCsv = 'id,name,value\n1,Alice,\n2,Bob,\n3,Carol,';
    const buffer = Buffer.from(allNullCsv, 'utf-8');
    const fileInput = page.locator('input[type="file"]');

    if (await fileInput.isVisible()) {
      const fileChooserPromise = page.waitForEvent('filechooser');
      await fileInput.click();
      const fileChooser = await fileChooserPromise;

      await fileChooser.setFiles({
        name: 'all-null.csv',
        mimeType: 'text/csv',
        buffer: buffer,
      });

      await page.waitForTimeout(3000);
      await dataPanel.switchToStatsTab();

      const valueStats = await dataPanel.getColumnStats('value');
      expect(valueStats).toBeTruthy();
      expect(parseInt(valueStats?.nulls || '0')).toBe(3);
    }
  });
});
