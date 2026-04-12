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

    await canvas.connectNodes(0, 2);
    await canvas.connectNodes(1, 2);

    // Check that both edges exist
    const edgeCount = await page.locator('.react-flow__edge').count();
    expect(edgeCount).toBe(2);
  });

  test('should configure join type', async ({ page }) => {
    await canvas.dragNodeToCanvas('combine');
    await canvas.clickNode(0);  // Use index

    // Look for join type selector
    const joinTypeSelect = page.locator('select[name="joinType"]');
    if (await joinTypeSelect.isVisible({ timeout: 5000 })) {
      const joinTypes = ['inner', 'left', 'right', 'full'];

      for (const type of joinTypes) {
        await canvas.selectDropdownOption(joinTypeSelect, type, { waitForOptions: false });
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

    // Execute both input nodes first - Phase 2 fix
    await canvas.execute();
    await canvas.waitForExecutionComplete();

    await canvas.dragNodeToCanvas('combine', { x: 400, y: 200 });

    await canvas.connectNodes(0, 2);
    await canvas.connectNodes(1, 2);
    await canvas.clickNode(2);  // Use index

    // Configure left key
    const leftKeySelect = page.locator('select[name="leftColumn"]');
    await canvas.selectDropdownOption(leftKeySelect, 'id');

    // Configure right key
    const rightKeySelect = page.locator('select[name="rightColumn"]');
    await canvas.selectDropdownOption(rightKeySelect, 'user_id');

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

    // Execute both input nodes first - Phase 2 fix
    await canvas.execute();
    await canvas.waitForExecutionComplete();

    await canvas.dragNodeToCanvas('combine', { x: 400, y: 200 });

    await canvas.connectNodes(0, 2);
    await canvas.connectNodes(1, 2);
    await canvas.clickNode(2);  // Use index

    // Configure as inner join
    const joinTypeSelect = page.locator('select[name="joinType"]');
    await canvas.selectDropdownOption(joinTypeSelect, 'inner');

    // Configure keys to ensure valid SQL
    await canvas.selectDropdownOption(page.locator('select[name="leftColumn"]'), 'id');
    await canvas.selectDropdownOption(page.locator('select[name="rightColumn"]'), 'user_id');

    await page.waitForTimeout(1000);

    await assertSqlPreviewContains(page, 'INNER JOIN');
  });

  test('should support union operation', async ({ page }) => {
    await canvas.dragNodeToCanvas('input', { x: 100, y: 100 });
    await canvas.dragNodeToCanvas('input', { x: 100, y: 300 });
    await canvas.dragNodeToCanvas('combine', { x: 400, y: 200 });

    await canvas.connectNodes(0, 1);
    await canvas.connectNodes(1, 2);
    await canvas.clickNode(2);  // Use index

    // Look for union option
    const joinTypeSelect = page.locator('select[name="joinType"]');
    if (await joinTypeSelect.isVisible({ timeout: 5000 })) {
      await canvas.selectDropdownOption(joinTypeSelect, 'union');
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

    // Execute input nodes first - Phase 2 fix
    await canvas.execute();
    await canvas.waitForExecutionComplete();

    await canvas.dragNodeToCanvas('combine', { x: 400, y: 200 });
    await canvas.dragNodeToCanvas('output', { x: 700, y: 200 });

    await canvas.connectNodes(0, 2);
    await canvas.connectNodes(1, 2);
    await canvas.connectNodes(2, 3);

    // Configure join
    await canvas.clickNode(2);  // Use index

    await canvas.selectDropdownOption(page.locator('select[name="joinType"]'), 'inner');
    await canvas.selectDropdownOption(page.locator('select[name="leftColumn"]'), 'id');
    await canvas.selectDropdownOption(page.locator('select[name="rightColumn"]'), 'user_id');

    await page.waitForTimeout(1000);

    // Execute
    await canvas.execute();
    await canvas.waitForExecutionComplete();

    // Check results
    await canvas.clickNode(3);  // Use index for output
    await page.waitForTimeout(1000);

    await dataPanel.switchToDataTab();

    // Wait for table to be visible with rows
    await expect(page.locator('table').first()).toBeVisible({ timeout: 5000 });
    await expect(page.locator('tbody tr').first()).toBeVisible({ timeout: 5000 });
  });
});
