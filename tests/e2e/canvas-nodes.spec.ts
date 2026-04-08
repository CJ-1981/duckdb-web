import { test, expect } from '@playwright/test';
import { WorkflowCanvas } from './pages/WorkflowCanvas';
import { DataInspectionPanel } from './pages/DataInspectionPanel';
import { uploadTestCsv, sampleCsvData } from './fixtures/testData';

/**
 * Node-Specific Tests
 *
 * These tests verify the functionality of individual node types
 * and their interactions with the canvas.
 */

test.describe('Canvas and Node Tests', () => {
  let canvas: WorkflowCanvas;
  let panel: DataInspectionPanel;

  test.beforeEach(async ({ page }) => {
    canvas = new WorkflowCanvas(page);
    panel = new DataInspectionPanel(page);

    await page.goto('');
    await canvas.waitForReady();
  });

  test('input node configuration', async ({ page }) => {
    // Add input node
    await canvas.dragNodeToCanvas('input');
    await canvas.selectNodeByIndex(0);

    // Upload CSV
    await uploadTestCsv(page, sampleCsvData);

    // Verify configuration panel is visible in properties panel
    const configPanel = page.locator('aside').filter({ hasText: 'Node Properties' });
    await expect(configPanel).toBeVisible();

    // Verify file name is displayed
    await expect(configPanel.locator(`text=${sampleCsvData.filename}`)).toBeVisible();
  });

  test('filter node configuration', async ({ page }) => {
    // Add input node with data
    await canvas.dragNodeToCanvas('input');
    await canvas.selectNodeByIndex(0);
    await uploadTestCsv(page, sampleCsvData);

    // Add filter node
    await canvas.dragNodeToCanvas('filter', { x: 300, y: 100 });

    // Connect input to filter using flexible labels
    await canvas.connectNodes(/input|csv/i, /filter/i);

    // Select filter node
    await canvas.clickNode(/filter/i);

    // Verify filter configuration options in properties panel
    const filterConfig = page.locator('aside').filter({ hasText: 'Node Properties' });
    await expect(filterConfig).toContainText(/Filter Configuration/i);
  });

  test('aggregate node configuration', async ({ page }) => {
    // Add input node
    await canvas.dragNodeToCanvas('input');
    await canvas.selectNodeByIndex(0);
    await uploadTestCsv(page, sampleCsvData);

    // Add aggregate node
    await canvas.dragNodeToCanvas('aggregate', { x: 300, y: 100 });

    // Connect nodes using flexible labels
    await canvas.connectNodes(/input|csv/i, /aggregate/i);

    // Select aggregate node
    await canvas.clickNode(/aggregate/i);

    // Verify aggregate configuration in properties panel
    const aggregateConfig = page.locator('aside').filter({ hasText: 'Node Properties' });
    await expect(aggregateConfig).toContainText(/Aggregate Data/i);
  });

  test('join node configuration', async ({ page }) => {
    // Add two input nodes
    await canvas.dragNodeToCanvas('input');
    await canvas.dragNodeToCanvas('input', { x: 50, y: 200 });

    // Add join node
    await canvas.dragNodeToCanvas('join', { x: 300, y: 150 });

    // Connect both inputs to join
    await canvas.connectNodes(/input|csv/i, /combine|join/i);

    // Select join node
    await canvas.clickNode(/combine|join/i);

    // Verify join configuration in properties panel
    const joinConfig = page.locator('aside').filter({ hasText: 'Node Properties' });
    await expect(joinConfig).toContainText(/Combine Datasets/i);
  });

  test('output node configuration', async ({ page }) => {
    // Add input and output nodes
    await canvas.dragNodeToCanvas('input');
    await canvas.dragNodeToCanvas('output', { x: 300, y: 100 });

    // Connect input to output
    await canvas.connectNodes(/input|csv/i, /export|output/i);

    // Select output node
    await canvas.clickNode(/export|output/i);

    // Verify output configuration in properties panel
    const outputConfig = page.locator('aside').filter({ hasText: 'Node Properties' });
    await expect(outputConfig).toBeVisible();
  });

  test.skip('can delete node from context menu', async ({ page }) => {
    // Add a node
    await canvas.dragNodeToCanvas('input');

    // Right-click on the node
    const node = canvas.nodeContainer.first();
    await node.click({ button: 'right' });

    // Click delete from context menu
    const deleteOption = page.locator('text=/delete|remove/i').first();
    await deleteOption.click();

    // Verify node was deleted
    const isEmpty = await canvas.isEmpty();
    expect(isEmpty).toBe(true);
  });

  test.skip('can duplicate node', async ({ page }) => {
    // Add a node
    await canvas.dragNodeToCanvas('input');

    const initialCount = await canvas.getNodeCount();

    // Right-click on the node
    const node = canvas.nodeContainer.first();
    await node.click({ button: 'right' });

    // Click duplicate from context menu
    const duplicateOption = page.locator('text=/duplicate|copy/i').first();
    await duplicateOption.click();

    // Verify node was duplicated
    expect(await canvas.getNodeCount()).toBe(initialCount + 1);
  });

  test('node displays row count after execution', async ({ page }) => {
    // Add input node
    await canvas.dragNodeToCanvas('input');
    await canvas.selectNodeByIndex(0);
    await uploadTestCsv(page, sampleCsvData);

    // Execute workflow
    await canvas.execute();
    await canvas.waitForExecutionComplete();

    // Verify row count is displayed on node using flexible label
    const rowCount = await canvas.getNodeRowCount(/input|csv/i);
    expect(rowCount).toMatch(/\d+/);
  });

  test('can connect nodes with valid connection', async ({ page }) => {
    // Add two nodes
    await canvas.dragNodeToCanvas('input');
    await canvas.dragNodeToCanvas('filter', { x: 300, y: 100 });

    // Connect them using flexible labels
    await canvas.connectNodes(/input|csv/i, /filter/i);

    // Verify connection exists (check for edge in DOM)
    const edge = page.locator('.react-flow__edge').first();
    await expect(edge).toBeVisible();
  });

  test('can disconnect nodes', async ({ page }) => {
    // Add and connect two nodes
    await canvas.dragNodeToCanvas('input');
    await canvas.dragNodeToCanvas('filter', { x: 300, y: 100 });
    await canvas.connectNodes(/input|csv/i, /filter/i);

    // Click on the edge to select it
    const edge = page.locator('.react-flow__edge').first();
    await edge.click();

    // Delete the connection
    await page.keyboard.press('Delete');

    // Verify edge was removed
    const edgeCount = await page.locator('.react-flow__edge').count();
    expect(edgeCount).toBe(0);
  });

  test('multiple nodes can be added and arranged', async ({ page }) => {
    // Add multiple nodes at different positions
    await canvas.dragNodeToCanvas('input');
    await canvas.dragNodeToCanvas('filter', { x: 300, y: 50 });
    await canvas.dragNodeToCanvas('aggregate', { x: 300, y: 200 });
    await canvas.dragNodeToCanvas('output', { x: 600, y: 125 });

    // Verify all nodes are present
    expect(await canvas.getNodeCount()).toBe(4);

    // Verify all nodes are visible
    const nodes = await canvas.getAllNodeLabels();
    expect(nodes.length).toBe(4);
  });
});
