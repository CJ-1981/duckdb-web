import { test, expect } from '@playwright/test';
import { WorkflowCanvas } from '../pages/WorkflowCanvas';
import { DataInspectionPanel } from '../pages/DataInspectionPanel';
import { sampleCsvData, ordersData } from '../fixtures/testData';
import { assertNodeExists, assertJoinConfigured, assertSqlPreviewContains, assertNodeCount } from '../fixtures/assertions';
import { uploadTestCsv } from '../fixtures/testData';

test.describe('Join Node Tests', () => {
  let canvas: WorkflowCanvas;
  let dataPanel: DataInspectionPanel;

  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    canvas = new WorkflowCanvas(page);
    dataPanel = new DataInspectionPanel(page);
    await canvas.waitForReady();
  });

  test('should create join node from palette', async ({ page }) => {
    await canvas.dragNodeToCanvas('combine');
    await expect(await canvas.getNodeCount()).toBe(1);
    await assertNodeExists(page, 'Join');
  });

  test('should allow two input connections', async ({ page }) => {
    await canvas.dragNodeToCanvas('input', { x: 100, y: 100 });
    await canvas.dragNodeToCanvas('input', { x: 100, y: 300 });
    await canvas.dragNodeToCanvas('combine', { x: 400, y: 200 });

    await assertNodeCount(page, 3);

    const nodes = await canvas.getAllNodeLabels();
    await canvas.connectNodes(nodes[0], nodes[2]);
    await canvas.connectNodes(nodes[1], nodes[2]);

    // Check that both edges exist
    const edgeCount = await page.locator('.react-flow__edge').count();
    expect(edgeCount).toBe(2);
  });

  test('should configure join type', async ({ page }) => {
    await canvas.dragNodeToCanvas('combine');
    await canvas.clickNode('Join');

    // Look for join type selector
    const joinTypeSelect = page.locator('select[name="joinType"]');
    if (await joinTypeSelect.isVisible()) {
      const joinTypes = ['inner', 'left', 'right', 'full'];

      for (const type of joinTypes) {
        await joinTypeSelect.selectOption(type);
        await page.waitForTimeout(500);

        const selectedValue = await joinTypeSelect.inputValue();
        expect(selectedValue).toBe(type);
      }
    }
  });

  test('should configure join keys', async ({ page }) => {
    await canvas.dragNodeToCanvas('input', { x: 100, y: 100 });
    await canvas.selectNodeByIndex(0);
    await uploadTestCsv(page, sampleCsvData);

    await canvas.dragNodeToCanvas('input', { x: 100, y: 300 });
    await canvas.selectNodeByIndex(1);
    await uploadTestCsv(page, ordersData);

    await canvas.dragNodeToCanvas('combine', { x: 400, y: 200 });

    const nodes = await canvas.getAllNodeLabels();
    await canvas.connectNodes(nodes[0], nodes[2]);
    await canvas.connectNodes(nodes[1], nodes[2]);

    await canvas.clickNode(nodes[2]);

    // Configure left key
    const leftKeySelect = page.locator('select[name="leftColumn"]');
    await leftKeySelect.waitFor({ state: 'visible' });
    await leftKeySelect.selectOption('id');

    // Configure right key
    const rightKeySelect = page.locator('select[name="rightColumn"]');
    await rightKeySelect.selectOption('user_id');

    await page.waitForTimeout(1000);

    await assertSqlPreviewContains(page, 'JOIN');
    await assertSqlPreviewContains(page, 'ON');
  });

  test('should generate correct SQL for inner join', async ({ page }) => {
    await canvas.dragNodeToCanvas('input', { x: 100, y: 100 });
    await canvas.selectNodeByIndex(0);
    await uploadTestCsv(page, sampleCsvData);

    await canvas.dragNodeToCanvas('input', { x: 100, y: 300 });
    await canvas.selectNodeByIndex(1);
    await uploadTestCsv(page, ordersData);

    await canvas.dragNodeToCanvas('combine', { x: 400, y: 200 });

    const nodes = await canvas.getAllNodeLabels();
    await canvas.connectNodes(nodes[0], nodes[2]);
    await canvas.connectNodes(nodes[1], nodes[2]);

    await canvas.clickNode(nodes[2]);

    // Configure as inner join
    const joinTypeSelect = page.locator('select[name="joinType"]');
    await joinTypeSelect.selectOption('inner');

    // Configure keys to ensure valid SQL
    await page.locator('select[name="leftColumn"]').selectOption('id');
    await page.locator('select[name="rightColumn"]').selectOption('user_id');

    await page.waitForTimeout(1000);

    await assertSqlPreviewContains(page, 'INNER JOIN');
  });

  test('should support union operation', async ({ page }) => {
    await canvas.dragNodeToCanvas('input', { x: 100, y: 100 });
    await canvas.dragNodeToCanvas('input', { x: 100, y: 300 });
    await canvas.dragNodeToCanvas('combine', { x: 400, y: 200 });

    const nodes = await canvas.getAllNodeLabels();
    await canvas.connectNodes(nodes[0], nodes[2]);
    await canvas.connectNodes(nodes[1], nodes[2]);

    await canvas.clickNode(nodes[2]);

    // Look for union option
    const joinTypeSelect = page.locator('select[name="joinType"]');
    if (await joinTypeSelect.isVisible()) {
      await joinTypeSelect.selectOption('union');
      await page.waitForTimeout(1000);
      await assertSqlPreviewContains(page, 'UNION');
    }
  });

  test('should display join results in data panel', async ({ page }) => {
    await canvas.dragNodeToCanvas('input', { x: 100, y: 100 });
    await canvas.selectNodeByIndex(0);
    await uploadTestCsv(page, sampleCsvData);

    await canvas.dragNodeToCanvas('input', { x: 100, y: 300 });
    await canvas.selectNodeByIndex(1);
    await uploadTestCsv(page, ordersData);

    await canvas.dragNodeToCanvas('combine', { x: 400, y: 200 });
    await canvas.dragNodeToCanvas('output', { x: 700, y: 200 });

    const nodes = await canvas.getAllNodeLabels();
    await canvas.connectNodes(nodes[0], nodes[2]);
    await canvas.connectNodes(nodes[1], nodes[2]);
    await canvas.connectNodes(nodes[2], nodes[3]);

    // Configure join
    await canvas.clickNode(nodes[2]);

    await page.locator('select[name="joinType"]').selectOption('inner');
    await page.locator('select[name="leftColumn"]').selectOption('id');
    await page.locator('select[name="rightColumn"]').selectOption('user_id');

    await page.waitForTimeout(1000);

    // Execute
    await canvas.execute();
    await canvas.waitForExecutionComplete();

    // Check results
    await canvas.clickNode(nodes[3]);
    await dataPanel.switchToDataTab();

    await expect(page.locator('table').first()).toBeVisible();
  });
});
