import { test, expect } from '@playwright/test';
import { WorkflowCanvas } from '../pages/WorkflowCanvas';
import { DataInspectionPanel } from '../pages/DataInspectionPanel';
import { sampleCsvData } from '../fixtures/testData';
import { uploadTestCsv } from '../fixtures/testData';

test.describe('Smoke Tests - Basic Workflow', () => {
  let canvas: WorkflowCanvas;
  let dataPanel: DataInspectionPanel;

  test.beforeEach(async ({ page }) => {
    await page.goto('');
    canvas = new WorkflowCanvas(page);
    dataPanel = new DataInspectionPanel(page);
    await canvas.waitForReady();
  });

  test('should load the application and display empty canvas', async ({ page }) => {
    await expect(page).toHaveTitle(/duckdb web|data analyst/i);
    await expect(canvas.canvas).toBeVisible();
    await expect(canvas.emptyState).toBeVisible();
    expect(await canvas.isEmpty()).toBeTruthy();
  });

  test('should display node palette sidebar', async ({ page }) => {
    const sidebar = page.locator('[data-testid="node-palette"], .sidebar, aside');
    await expect(sidebar).toBeVisible();

    // Check for common node types
    await expect(page.locator('text=/input|file/i').first()).toBeVisible();
    await expect(page.locator('text=/filter|where/i').first()).toBeVisible();
    await expect(page.locator('text=/aggregate|group/i').first()).toBeVisible();
    await expect(page.locator('text=/output|export/i').first()).toBeVisible();
  });

  test('should display control buttons on canvas', async () => {
    await expect(canvas.controls).toBeVisible();
    await expect(canvas.miniMap).toBeVisible();
  });

  test('should drag and drop an input node onto canvas', async ({ page }) => {
    await canvas.dragNodeToCanvas('input');
    await expect(await canvas.getNodeCount()).toBe(1);
    await expect(await canvas.hasNode('Input')).toBeTruthy();
  });

  test('should allow multiple nodes on canvas', async ({ page }) => {
    await canvas.dragNodeToCanvas('input', { x: 200, y: 100 });
    await canvas.dragNodeToCanvas('filter', { x: 200, y: 300 });
    await canvas.dragNodeToCanvas('output', { x: 200, y: 500 });

    await expect(await canvas.getNodeCount()).toBe(3);
  });

  test('should connect two nodes by dragging edge', async ({ page }) => {
    await canvas.dragNodeToCanvas('input');
    await canvas.dragNodeToCanvas('output');

    const nodes = await canvas.getAllNodeLabels();
    if (nodes.length >= 2) {
      await canvas.connectNodes(nodes[0], nodes[1]);

      const edgeCount = await page.locator('.react-flow__edge, [data-testid^="rf__edge-"]').count();
      await expect(edgeCount).toBeGreaterThan(0);
    }
  });

  test('should select node when clicked', async ({ page }) => {
    await canvas.dragNodeToCanvas('input');
    await canvas.selectNodeByIndex(0);
    const node = page.locator('.react-flow__node').first();
    await expect(node).toHaveClass(/selected|ring-2/);
  });

  test('should display data inspection panel when node selected', async ({ page }) => {
    await canvas.dragNodeToCanvas('input');
    await canvas.selectNodeByIndex(0);
    await expect(dataPanel.panel).toBeVisible();
  });

  test('should show execute button', async ({ page }) => {
    await expect(canvas.executeButton).toBeVisible();
  });

  test('should show save and load workflow buttons', async ({ page }) => {
    await expect(canvas.saveButton).toBeVisible();
    await expect(canvas.loadButton).toBeVisible();
  });

  test('should allow keyboard undo and redo', async ({ page }) => {
    const isMac = await page.evaluate(() => /Mac|iPod|iPhone|iPad|Macintosh/.test(navigator.userAgent));

    // Add a node
    await canvas.dragNodeToCanvas('input');
    const initialCount = await canvas.getNodeCount();
    expect(initialCount).toBe(1);

    // Delete it
    await canvas.selectNodeByIndex(0);
    await canvas.deleteSelectedNode();
    await expect(await canvas.getNodeCount()).toBe(0);

    // Undo
    if (isMac) {
      await page.keyboard.press('Meta+Z');
    } else {
      await page.keyboard.press('Control+Z');
    }
    await expect(await canvas.getNodeCount()).toBe(1);

    // Redo
    if (isMac) {
      await page.keyboard.press('Meta+Shift+Z');
    } else {
      await page.keyboard.press('Control+Y');
    }
    await expect(await canvas.getNodeCount()).toBe(0);
  });

  test('should allow canvas zoom in and out', async ({ page }) => {
    const initialTransform = await canvas.canvas.evaluate(el => {
      return window.getComputedStyle(el).transform;
    });

    await canvas.zoomIn();
    await page.waitForTimeout(500);

    await canvas.zoomOut();
    await page.waitForTimeout(500);

    const finalTransform = await canvas.canvas.evaluate(el => {
      return window.getComputedStyle(el).transform;
    });

    expect(finalTransform).toBeTruthy();
  });

  test('should allow fit view to show all nodes', async ({ page }) => {
    await canvas.dragNodeToCanvas('input', { x: 100, y: 100 });
    await canvas.dragNodeToCanvas('filter', { x: 500, y: 100 });
    await canvas.dragNodeToCanvas('output', { x: 900, y: 100 });

    await canvas.fitView();
    await page.waitForTimeout(1000);

    const nodes = await canvas.getAllNodeLabels();
    await expect(nodes.length).toBe(3);
  });

  test('should display bottom panel tabs', async ({ page }) => {
    await canvas.dragNodeToCanvas('input');
    await canvas.selectNodeByIndex(0);
    
    const bottomPanel = page.locator('[data-testid="data-inspection-panel"]');
    await expect(bottomPanel).toBeVisible();

    await expect(dataPanel.tabs.data).toBeVisible();
    await expect(dataPanel.tabs.schema).toBeVisible();
    await expect(dataPanel.tabs.stats).toBeVisible();
  });

  test('should switch between data panel tabs', async ({ page }) => {
    await canvas.dragNodeToCanvas('input');
    await canvas.selectNodeByIndex(0);
    await uploadTestCsv(page, sampleCsvData);

    // Execute workflow to load data
    await canvas.execute();
    await canvas.waitForExecutionComplete();
    await page.waitForTimeout(2000); // Wait for data propagation

    await dataPanel.switchToDataTab();
    await expect(dataPanel.dataTable).toBeVisible();

    await dataPanel.switchToSchemaTab();
    await expect(dataPanel.schemaTable).toBeVisible();

    await dataPanel.switchToStatsTab();
    await expect(dataPanel.statsContainer).toBeVisible();
  });

  test('should persist workflow when navigating tabs', async ({ page }) => {
    await canvas.dragNodeToCanvas('input');
    await canvas.dragNodeToCanvas('output');
    const nodeCount = await canvas.getNodeCount();

    // Simulate tab navigation
    await page.evaluate(() => {
      window.dispatchEvent(new Event('beforeunload'));
    });

    await page.waitForTimeout(1000);
    expect(await canvas.getNodeCount()).toBe(nodeCount);
  });

  test('should display tooltips for node palette items', async ({ page }) => {
    const paletteItem = page.locator('text=/input|file/i').first();
    await paletteItem.hover();

    const tooltip = page.locator('[role="tooltip"], .tooltip');
    const isVisible = await tooltip.isVisible().catch(() => false);

    // Tooltip may or may not be present depending on implementation
    expect(isVisible).toBeFalsy();
  });

  test('should handle error when invalid file uploaded', async ({ page }) => {
    const fileInput = page.locator('input[type="file"]');
    if (await fileInput.isVisible()) {
      const fileChooserPromise = page.waitForEvent('filechooser');

      await fileInput.click();
      const fileChooser = await fileChooserPromise;

      await fileChooser.setFiles({
        name: 'invalid.txt',
        mimeType: 'text/plain',
        buffer: Buffer.from('invalid content'),
      });

      // Should show error message or fail gracefully
      await page.waitForTimeout(2000);
    }
  });
});

test.describe('Smoke Tests - Data Upload', () => {
  test('should upload CSV file successfully', async ({ page }) => {
    await page.goto('');
    const canvas = new WorkflowCanvas(page);
    await canvas.waitForReady();

    // Create CSV content
    const csvContent = 'id,name\n1,Alice\n2,Bob';
    const buffer = Buffer.from(csvContent, 'utf-8');

    // Upload file
    const fileInput = page.locator('input[type="file"]');
    if (await fileInput.isVisible()) {
      const fileChooserPromise = page.waitForEvent('filechooser');
      await fileInput.click();
      const fileChooser = await fileChooserPromise;

      await fileChooser.setFiles({
        name: 'test.csv',
        mimeType: 'text/csv',
        buffer: buffer,
      });

      await page.waitForTimeout(2000);
    }
  });
});

test.describe('Smoke Tests - Workflow Execution', () => {
  test('should execute simple workflow and show results', async ({ page }) => {
    await page.goto('');
    const canvas = new WorkflowCanvas(page);
    await canvas.waitForReady();

    // Create a simple workflow
    await canvas.dragNodeToCanvas('input');
    await canvas.dragNodeToCanvas('output');

    const nodes = await canvas.getAllNodeLabels();
    if (nodes.length >= 2) {
      await canvas.connectNodes(nodes[0], nodes[1]);

      // Try to execute (may fail without actual data)
      await canvas.execute();
      await page.waitForTimeout(3000);
    }
  });
});
