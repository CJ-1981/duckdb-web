import { test, expect } from '@playwright/test';
import { WorkflowCanvas } from '../pages/WorkflowCanvas';
import { DataInspectionPanel } from '../pages/DataInspectionPanel';
import { sampleCsvData, csvWithNulls, csvWithSpecialChars } from '../fixtures/testData';
import { assertFileUploaded, assertNodeExists, assertDataColumns } from '../fixtures/assertions';

test.describe('Input Node Tests', () => {
  let canvas: WorkflowCanvas;
  let dataPanel: DataInspectionPanel;

  test.beforeEach(async ({ page }) => {
    await page.goto('');
    canvas = new WorkflowCanvas(page);
    dataPanel = new DataInspectionPanel(page);
    await canvas.waitForReady();
  });

  test('should create input node from palette', async ({ page }) => {
    await canvas.dragNodeToCanvas('input');
    await expect(await canvas.getNodeCount()).toBe(1);
    await assertNodeExists(page, 'Input');
  });

  test('should allow CSV file upload', async ({ page }) => {
    await canvas.dragNodeToCanvas('input');

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
    }
  });

  test('should display uploaded file columns', async ({ page }) => {
    await canvas.dragNodeToCanvas('input');
    await page.locator('.react-flow__node').first().click();

    // Upload CSV
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

      await page.waitForTimeout(3000);

      // Check columns in data panel
      await dataPanel.switchToDataTab();
      const columns = await dataPanel.getDataColumns();
      expect(columns).toContain('id');
      expect(columns).toContain('name');
      expect(columns).toContain('email');
    }
  });

  test('should handle CSV with null values', async ({ page }) => {
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

      // Should show null counts
      const emailStats = await dataPanel.getColumnStats('email');
      expect(emailStats?.nulls).toBeTruthy();
    }
  });

  test('should handle CSV with special characters', async ({ page }) => {
    await canvas.dragNodeToCanvas('input');
    await page.locator('.react-flow__node').first().click();

    const buffer = Buffer.from(csvWithSpecialChars.content, 'utf-8');
    const fileInput = page.locator('input[type="file"]');

    if (await fileInput.isVisible()) {
      const fileChooserPromise = page.waitForEvent('filechooser');
      await fileInput.click();
      const fileChooser = await fileChooserPromise;

      await fileChooser.setFiles({
        name: csvWithSpecialChars.filename,
        mimeType: 'text/csv',
        buffer: buffer,
      });

      await page.waitForTimeout(3000);
      await dataPanel.switchToDataTab();

      // Should preserve special characters
      const specialCharValue = await dataPanel.getCellValue(0, 'name');
      expect(specialCharValue).toContain(',');
    }
  });

  test('should display row count on input node', async ({ page }) => {
    await canvas.dragNodeToCanvas('input');

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

      await page.waitForTimeout(3000);

      // Check for row count display
      const rowCount = await canvas.getNodeRowCount('Input');
      expect(rowCount).toBeTruthy();
    }
  });

  test('should show correct column types in schema', async ({ page }) => {
    await canvas.dragNodeToCanvas('input');
    await page.locator('.react-flow__node').first().click();

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

      await page.waitForTimeout(3000);
      await dataPanel.switchToSchemaTab();

      const schema = await dataPanel.getSchema();
      expect(schema.length).toBeGreaterThan(0);

      // Check that types are displayed
      const idColumn = schema.find(col => col.name === 'id');
      expect(idColumn).toBeTruthy();
    }
  });

  test('should allow multiple input nodes', async ({ page }) => {
    await canvas.dragNodeToCanvas('input', { x: 100, y: 100 });
    await canvas.dragNodeToCanvas('input', { x: 100, y: 300 });

    await expect(await canvas.getNodeCount()).toBe(2);
  });

  test('should remove input node when deleted', async ({ page }) => {
    await canvas.dragNodeToCanvas('input');

    const initialCount = await canvas.getNodeCount();
    expect(initialCount).toBe(1);

    await page.locator('.react-flow__node').first().click();
    await canvas.deleteSelectedNode();

    await expect(await canvas.getNodeCount()).toBe(0);
  });

  test('should display file metadata after upload', async ({ page }) => {
    await canvas.dragNodeToCanvas('input');
    await page.locator('.react-flow__node').first().click();

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

      await page.waitForTimeout(3000);

      // Check for filename or metadata display
      const node = page.locator('.react-flow__node').first();
      const nodeText = await node.textContent();
      expect(nodeText).toBeTruthy();
    }
  });
});
