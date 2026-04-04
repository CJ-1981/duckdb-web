import { test, expect } from '@playwright/test';
import { WorkflowCanvas } from './pages/WorkflowCanvas';
import { DataInspectionPanel } from './pages/DataInspectionPanel';
import { uploadTestCsv, getAllTestDatasets } from './fixtures/testData';

/**
 * Smoke Tests - Basic application functionality verification
 *
 * These tests verify that the application loads and basic features work.
 * They are designed to be fast and catch fundamental issues.
 */

test.describe('Smoke Tests', () => {
  let canvas: WorkflowCanvas;
  let panel: DataInspectionPanel;

  test.beforeEach(async ({ page }) => {
    canvas = new WorkflowCanvas(page);
    panel = new DataInspectionPanel(page);

    // Navigate to the application
    await page.goto('http://localhost:3000');

    // Wait for the canvas to be ready
    await canvas.waitForReady();
  });

  test('application loads successfully', async ({ page }) => {
    // Verify the page title
    await expect(page).toHaveTitle(/DuckDB Web|Data Analyst/);

    // Verify the canvas is visible
    await expect(canvas.canvas).toBeVisible();

    // Verify the empty state message
    await expect(canvas.emptyState).toBeVisible();
  });

  test('canvas starts empty', async () => {
    // Verify the canvas is empty
    const isEmpty = await canvas.isEmpty();
    expect(isEmpty).toBe(true);
  });

  test('node palette is visible', async ({ page }) => {
    // Verify the node palette/sidebar exists
    const palette = page.locator('[data-testid*="palette"], .node-palette, aside').first();
    await expect(palette).toBeVisible();
  });

  test('can add a node to canvas', async ({ page }) => {
    // Add an input node
    await canvas.dragNodeToCanvas('input');

    // Verify the node was added
    const nodeCount = await canvas.getNodeCount();
    expect(nodeCount).toBeGreaterThan(0);

    // Verify the canvas is no longer empty
    const isEmpty = await canvas.isEmpty();
    expect(isEmpty).toBe(false);
  });

  test('can select a node', async ({ page }) => {
    // Add a node
    await canvas.dragNodeToCanvas('input');

    // Select the first node
    await canvas.selectNodeByIndex(0);

    // Verify the data inspection panel becomes visible
    await panel.waitForVisible();
  });

  test('mini map and controls are visible', async () => {
    // Add some nodes to populate the canvas
    await canvas.dragNodeToCanvas('input');
    await canvas.dragNodeToCanvas('filter', { x: 300, y: 200 });

    // Verify controls are visible
    await expect(canvas.controls).toBeVisible();
  });

  test('can upload CSV file', async ({ page }) => {
    // Get a test dataset
    const datasets = getAllTestDatasets();
    const testDataset = datasets[0];

    // Click on the input node to configure it
    await canvas.dragNodeToCanvas('input');
    await canvas.selectNodeByIndex(0);

    // Upload the CSV file
    await uploadTestCsv(page, testDataset);

    // Verify the file was uploaded (check for success message or file name display)
    const successIndicator = page.locator('text=/uploaded|loaded|success/i').first();
    await expect(successIndicator).toBeVisible({ timeout: 10000 });
  });

  test('can undo node addition', async ({ page }) => {
    // Get initial node count
    const initialCount = await canvas.getNodeCount();

    // Add a node
    await canvas.dragNodeToCanvas('input');

    // Verify node was added
    expect(await canvas.getNodeCount()).toBe(initialCount + 1);

    // Undo
    await canvas.undo();

    // Verify node was removed
    expect(await canvas.getNodeCount()).toBe(initialCount);
  });

  test('can redo after undo', async ({ page }) => {
    // Add a node
    await canvas.dragNodeToCanvas('input');

    // Undo
    await canvas.undo();

    // Redo
    await canvas.redo();

    // Verify node is back
    expect(await canvas.getNodeCount()).toBeGreaterThan(0);
  });

  test('keyboard shortcuts work', async ({ page }) => {
    // Add a node
    await canvas.dragNodeToCanvas('input');

    // Select the node
    await canvas.selectNodeByIndex(0);

    // Delete the node using keyboard
    await canvas.deleteSelectedNode();

    // Verify node was deleted
    const isEmpty = await canvas.isEmpty();
    expect(isEmpty).toBe(true);
  });
});
