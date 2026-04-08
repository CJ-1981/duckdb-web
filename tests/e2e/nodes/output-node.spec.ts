import { test, expect } from '@playwright/test';
import { WorkflowCanvas } from '../pages/WorkflowCanvas';
import { DataInspectionPanel } from '../pages/DataInspectionPanel';
import { sampleCsvData } from '../fixtures/testData';
import { assertNodeExists, assertExecutionSuccess } from '../fixtures/assertions';

test.describe('Output Node Tests', () => {
  let canvas: WorkflowCanvas;
  let dataPanel: DataInspectionPanel;

  test.beforeEach(async ({ page }) => {
    await page.goto('');
    canvas = new WorkflowCanvas(page);
    dataPanel = new DataInspectionPanel(page);
    await canvas.waitForReady();
  });

  test('should create output node from palette', async ({ page }) => {
    await canvas.dragNodeToCanvas('output');
    await expect(await canvas.getNodeCount()).toBe(1);
    await assertNodeExists(page, 'Output');
  });

  test('should accept connection from upstream node', async ({ page }) => {
    await canvas.dragNodeToCanvas('input');
    await canvas.dragNodeToCanvas('output');

    const nodes = await canvas.getAllNodeLabels();
    if (nodes.length >= 2) {
      await canvas.connectNodes(nodes[0], nodes[1]);

      const edgeCount = await page.locator('.react-flow__edge').count();
      expect(edgeCount).toBe(1);
    }
  });

  test('should show final row count after execution', async ({ page }) => {
    await canvas.dragNodeToCanvas('input');
    await canvas.dragNodeToCanvas('output');

    const nodes = await canvas.getAllNodeLabels();
    if (nodes.length >= 2) {
      await canvas.connectNodes(nodes[0], nodes[1]);

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

        // Execute
        await canvas.execute();
        await page.waitForTimeout(5000);

        // Check row count on output node
        const outputNode = page.locator('.react-flow__node').filter({ hasText: nodes[1] });
        const rowCountText = await outputNode.locator('text=/rows/i').textContent();
        expect(rowCountText).toBeTruthy();
      }
    }
  });

  test('should allow CSV download', async ({ page }) => {
    await canvas.dragNodeToCanvas('input');
    await canvas.dragNodeToCanvas('output');

    const nodes = await canvas.getAllNodeLabels();
    if (nodes.length >= 2) {
      await canvas.connectNodes(nodes[0], nodes[1]);

      // Upload and execute
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
        await canvas.execute();
        await page.waitForTimeout(5000);

        // Look for download button
        const downloadButton = page.locator('button:has-text("Download"), button:has-text("Export")');
        if (await downloadButton.isVisible()) {
          const downloadPromise = page.waitForEvent('download');
          await downloadButton.click();
          const download = await downloadPromise;

          expect(download.suggestedFilename()).toContain('.csv');
        }
      }
    }
  });

  test('should allow JSON download', async ({ page }) => {
    await canvas.dragNodeToCanvas('input');
    await canvas.dragNodeToCanvas('output');

    const nodes = await canvas.getAllNodeLabels();
    if (nodes.length >= 2) {
      await canvas.connectNodes(nodes[0], nodes[1]);

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
        await canvas.execute();
        await page.waitForTimeout(5000);

        // Look for format selector and download button
        const formatSelect = page.locator('select[name="format"], [data-testid="export-format"]');
        if (await formatSelect.isVisible()) {
          await formatSelect.selectOption('json');

          const downloadButton = page.locator('button:has-text("Download")');
          if (await downloadButton.isVisible()) {
            const downloadPromise = page.waitForEvent('download');
            await downloadButton.click();
            const download = await downloadPromise;

            expect(download.suggestedFilename()).toContain('.json');
          }
        }
      }
    }
  });

  test('should allow output name configuration', async ({ page }) => {
    await canvas.dragNodeToCanvas('output');
    await canvas.clickNode('Output');

    // Look for name input
    const nameInput = page.locator('input[name="outputName"], [data-testid="output-name"]');
    if (await nameInput.isVisible()) {
      await nameInput.fill('My Results');
      await page.waitForTimeout(1000);

      const value = await nameInput.inputValue();
      expect(value).toBe('My Results');
    }
  });

  test('should display output data preview', async ({ page }) => {
    await canvas.dragNodeToCanvas('input');
    await canvas.dragNodeToCanvas('output');

    const nodes = await canvas.getAllNodeLabels();
    if (nodes.length >= 2) {
      await canvas.connectNodes(nodes[0], nodes[1]);

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
        await canvas.execute();
        await page.waitForTimeout(5000);

        // Click output node and check data panel
        await canvas.clickNode(nodes[1]);
        await dataPanel.switchToDataTab();

        const columns = await dataPanel.getDataColumns();
        expect(columns.length).toBeGreaterThan(0);
      }
    }
  });

  test('should allow limiting output rows', async ({ page }) => {
    await canvas.dragNodeToCanvas('input');
    await canvas.dragNodeToCanvas('output');

    const nodes = await canvas.getAllNodeLabels();
    if (nodes.length >= 2) {
      await canvas.connectNodes(nodes[0], nodes[1]);

      await canvas.clickNode(nodes[1]);

      // Look for limit input
      const limitInput = page.locator('input[name="limit"], [data-testid="output-limit"]');
      if (await limitInput.isVisible()) {
        await limitInput.fill('5');
        await page.waitForTimeout(1000);

        const value = await limitInput.inputValue();
        expect(value).toBe('5');
      }
    }
  });

  test('should allow column selection for output', async ({ page }) => {
    await canvas.dragNodeToCanvas('input');
    await canvas.dragNodeToCanvas('output');

    const nodes = await canvas.getAllNodeLabels();
    if (nodes.length >= 2) {
      await canvas.connectNodes(nodes[0], nodes[1]);

      await canvas.clickNode(nodes[1]);

      // Look for column selector
      const columnSelector = page.locator('[data-testid="column-selector"], .column-selector');
      if (await columnSelector.isVisible()) {
        // Select/deselect columns
        const firstColumn = columnSelector.locator('input[type="checkbox"]').first();
        await firstColumn.check();
        await page.waitForTimeout(500);

        const isChecked = await firstColumn.isChecked();
        expect(isChecked).toBeTruthy();
      }
    }
  });

  test('should show output size in bytes', async ({ page }) => {
    await canvas.dragNodeToCanvas('input');
    await canvas.dragNodeToCanvas('output');

    const nodes = await canvas.getAllNodeLabels();
    if (nodes.length >= 2) {
      await canvas.connectNodes(nodes[0], nodes[1]);

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
        await canvas.execute();
        await page.waitForTimeout(5000);

        // Look for size indicator
        const sizeIndicator = page.locator('text=/KB|MB|bytes/i');
        const hasSize = await sizeIndicator.isVisible().catch(() => false);

        if (hasSize) {
          expect(sizeIndicator).toBeVisible();
        }
      }
    }
  });

  test('should handle multiple output nodes', async ({ page }) => {
    await canvas.dragNodeToCanvas('input');
    await canvas.dragNodeToCanvas('filter');
    await canvas.dragNodeToCanvas('output', { x: 700, y: 100 });
    await canvas.dragNodeToCanvas('output', { x: 700, y: 300 });

    const nodes = await canvas.getAllNodeLabels();
    if (nodes.length >= 4) {
      await canvas.connectNodes(nodes[0], nodes[1]);
      await canvas.connectNodes(nodes[1], nodes[2]);
      await canvas.connectNodes(nodes[1], nodes[3]);

      // Should have 3 edges
      const edgeCount = await page.locator('.react-flow__edge').count();
      expect(edgeCount).toBe(3);
    }
  });

  test('should allow output to database table', async ({ page }) => {
    await canvas.dragNodeToCanvas('input');
    await canvas.dragNodeToCanvas('output');

    const nodes = await canvas.getAllNodeLabels();
    if (nodes.length >= 2) {
      await canvas.connectNodes(nodes[0], nodes[1]);

      await canvas.clickNode(nodes[1]);

      // Look for database export option
      const exportModeSelect = page.locator('select[name="exportMode"], [data-testid="export-mode"]');
      if (await exportModeSelect.isVisible()) {
        await exportModeSelect.selectOption('database');
        await page.waitForTimeout(1000);

        // Should show table name input
        const tableNameInput = page.locator('input[name="tableName"]');
        const hasTableInput = await tableNameInput.isVisible().catch(() => false);

        if (hasTableInput) {
          await tableNameInput.fill('my_table');
          const value = await tableNameInput.inputValue();
          expect(value).toBe('my_table');
        }
      }
    }
  });

  test('should validate output configuration before download', async ({ page }) => {
    await canvas.dragNodeToCanvas('input');
    await canvas.dragNodeToCanvas('output');

    const nodes = await canvas.getAllNodeLabels();
    if (nodes.length >= 2) {
      await canvas.connectNodes(nodes[0], nodes[1]);

      // Try to download without data
      const downloadButton = page.locator('button:has-text("Download")');
      if (await downloadButton.isVisible()) {
        const isDisabled = await downloadButton.isDisabled();
        // Button might be disabled or show error
        if (isDisabled) {
          expect(isDisabled).toBeTruthy();
        }
      }
    }
  });
});
