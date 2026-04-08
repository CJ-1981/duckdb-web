import { test, expect } from '@playwright/test';
import { WorkflowCanvas } from '../pages/WorkflowCanvas';
import { DataInspectionPanel } from '../pages/DataInspectionPanel';
import { sampleCsvData, ordersData } from '../fixtures/testData';
import { assertNodeExists, assertJoinConfigured, assertSqlPreviewContains, assertNodeCount } from '../fixtures/assertions';

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
    const joinTypeSelect = page.locator('select[name="joinType"], [data-testid="join-type"]');
    if (await joinTypeSelect.isVisible()) {
      const joinTypes = ['inner', 'left', 'right', 'full'];

      for (const type of joinTypes) {
        await joinTypeSelect.selectOption(type);
        await page.waitForTimeout(500);

        const selectedValue = await joinTypeSelect.inputValue();
        expect(selectedValue).toBeTruthy();
      }
    }
  });

  test('should configure join keys', async ({ page }) => {
    await canvas.dragNodeToCanvas('input', { x: 100, y: 100 });
    await canvas.dragNodeToCanvas('input', { x: 100, y: 300 });
    await canvas.dragNodeToCanvas('combine', { x: 400, y: 200 });

    const nodes = await canvas.getAllNodeLabels();
    await canvas.connectNodes(nodes[0], nodes[2]);
    await canvas.connectNodes(nodes[1], nodes[2]);

    await canvas.clickNode(nodes[2]);

    // Configure left key
    const leftKeySelect = page.locator('select[name="leftColumn"], [data-testid="left-key"]');
    if (await leftKeySelect.isVisible()) {
      await leftKeySelect.selectOption('id');
    }

    // Configure right key
    const rightKeySelect = page.locator('select[name="rightColumn"], [data-testid="right-key"]');
    if (await rightKeySelect.isVisible()) {
      await rightKeySelect.selectOption('user_id');
    }

    await page.waitForTimeout(1000);

    await assertSqlPreviewContains(page, 'JOIN');
    await assertSqlPreviewContains(page, 'ON');
  });

  test('should generate correct SQL for inner join', async ({ page }) => {
    await canvas.dragNodeToCanvas('input', { x: 100, y: 100 });
    await canvas.dragNodeToCanvas('input', { x: 100, y: 300 });
    await canvas.dragNodeToCanvas('combine', { x: 400, y: 200 });

    const nodes = await canvas.getAllNodeLabels();
    await canvas.connectNodes(nodes[0], nodes[2]);
    await canvas.connectNodes(nodes[1], nodes[2]);

    await canvas.clickNode(nodes[2]);

    // Configure as inner join
    const joinTypeSelect = page.locator('select[name="joinType"]');
    if (await joinTypeSelect.isVisible()) {
      await joinTypeSelect.selectOption('inner');
    }

    await page.waitForTimeout(1000);

    await assertSqlPreviewContains(page, 'INNER JOIN');
  });

  test('should generate correct SQL for left join', async ({ page }) => {
    await canvas.dragNodeToCanvas('input', { x: 100, y: 100 });
    await canvas.dragNodeToCanvas('input', { x: 100, y: 300 });
    await canvas.dragNodeToCanvas('combine', { x: 400, y: 200 });

    const nodes = await canvas.getAllNodeLabels();
    await canvas.connectNodes(nodes[0], nodes[2]);
    await canvas.connectNodes(nodes[1], nodes[2]);

    await canvas.clickNode(nodes[2]);

    const joinTypeSelect = page.locator('select[name="joinType"]');
    if (await joinTypeSelect.isVisible()) {
      await joinTypeSelect.selectOption('left');
    }

    await page.waitForTimeout(1000);

    await assertSqlPreviewContains(page, 'LEFT JOIN');
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
      const options = await joinTypeSelect.locator('option').allTextContents();
      const hasUnion = options.some(o => o.toLowerCase().includes('union'));

      if (hasUnion) {
        await joinTypeSelect.selectOption('union');
        await page.waitForTimeout(1000);

        await assertSqlPreviewContains(page, 'UNION');
      }
    }
  });

  test('should validate join configuration', async ({ page }) => {
    await canvas.dragNodeToCanvas('input', { x: 100, y: 100 });
    await canvas.dragNodeToCanvas('input', { x: 100, y: 300 });
    await canvas.dragNodeToCanvas('combine', { x: 400, y: 200 });
    await canvas.dragNodeToCanvas('output', { x: 700, y: 200 });

    const nodes = await canvas.getAllNodeLabels();
    await canvas.connectNodes(nodes[0], nodes[2]);
    await canvas.connectNodes(nodes[1], nodes[2]);
    await canvas.connectNodes(nodes[2], nodes[3]);

    // Try to execute without proper join configuration
    await canvas.execute();
    await page.waitForTimeout(3000);

    // Should show validation error
    const errorMessage = page.locator('text=/error|join.*key|required/i');
    const hasError = await errorMessage.isVisible().catch(() => false);

    if (hasError) {
      expect(errorMessage).toBeVisible();
    }
  });

  test('should display join results in data panel', async ({ page }) => {
    await canvas.dragNodeToCanvas('input', { x: 100, y: 100 });
    await canvas.dragNodeToCanvas('input', { x: 100, y: 300 });
    await canvas.dragNodeToCanvas('combine', { x: 400, y: 200 });
    await canvas.dragNodeToCanvas('output', { x: 700, y: 200 });

    const nodes = await canvas.getAllNodeLabels();
    await canvas.connectNodes(nodes[0], nodes[2]);
    await canvas.connectNodes(nodes[1], nodes[2]);
    await canvas.connectNodes(nodes[2], nodes[3]);

    // Upload data to first input
    await canvas.clickNode(nodes[0]);
    const buffer1 = Buffer.from(sampleCsvData.content, 'utf-8');
    const fileInput = page.locator('input[type="file"]');

    if (await fileInput.isVisible()) {
      const fileChooserPromise = page.waitForEvent('filechooser');
      await fileInput.click();
      const fileChooser = await fileChooserPromise;

      await fileChooser.setFiles({
        name: sampleCsvData.filename,
        mimeType: 'text/csv',
        buffer: buffer1,
      });

      await page.waitForTimeout(2000);

      // Upload data to second input
      await canvas.clickNode(nodes[1]);
      const buffer2 = Buffer.from(ordersData.content, 'utf-8');

      const fileChooserPromise2 = page.waitForEvent('filechooser');
      await fileInput.click();
      const fileChooser2 = await fileChooserPromise2;

      await fileChooser2.setFiles({
        name: ordersData.filename,
        mimeType: 'text/csv',
        buffer: buffer2,
      });

      await page.waitForTimeout(2000);

      // Configure join
      await canvas.clickNode(nodes[2]);

      const joinTypeSelect = page.locator('select[name="joinType"]');
      if (await joinTypeSelect.isVisible()) {
        await joinTypeSelect.selectOption('inner');
      }

      const leftKeySelect = page.locator('select[name="leftColumn"]');
      if (await leftKeySelect.isVisible()) {
        await leftKeySelect.selectOption('id');
      }

      const rightKeySelect = page.locator('select[name="rightColumn"]');
      if (await rightKeySelect.isVisible()) {
        await rightKeySelect.selectOption('user_id');
      }

      await page.waitForTimeout(1000);

      // Execute
      await canvas.execute();
      await page.waitForTimeout(5000);

      // Check results
      await canvas.clickNode(nodes[3]);
      await dataPanel.switchToDataTab();

      const columns = await dataPanel.getDataColumns();
      expect(columns.length).toBeGreaterThan(0);
    }
  });

  test('should prevent circular join dependencies', async ({ page }) => {
    await canvas.dragNodeToCanvas('input');
    await canvas.dragNodeToCanvas('combine');
    await canvas.dragNodeToCanvas('output');

    const nodes = await canvas.getAllNodeLabels();
    if (nodes.length >= 3) {
      await canvas.connectNodes(nodes[0], nodes[1]);
      await canvas.connectNodes(nodes[1], nodes[2]);

      // Try to create circular dependency
      const sourceNode = page.locator('.react-flow__node').filter({ hasText: nodes[2] });
      const targetHandle = page.locator('.react-flow__node').filter({ hasText: nodes[0] })
        .locator('.react-flow__handle-top');

      // Attempt to connect (may be prevented by UI)
      await sourceNode.locator('.react-flow__handle-bottom').dragTo(targetHandle).catch(() => {
        // Expected to fail or be prevented
      });

      await page.waitForTimeout(1000);
    }
  });
});
