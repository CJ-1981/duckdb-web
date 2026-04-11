import { test, expect } from '@playwright/test';
import { WorkflowCanvas } from '../pages/WorkflowCanvas';
import { DataInspectionPanel } from '../pages/DataInspectionPanel';
import { csvWithNulls } from '../fixtures/testData';
import { assertColumnStatsExist, assertNullValueHandled } from '../fixtures/assertions';
import { uploadTestCsv } from '../fixtures/testData';

test.describe('Edge Cases - Null Handling', () => {
  let canvas: WorkflowCanvas;
  let dataPanel: DataInspectionPanel;

  test.beforeEach(async ({ page }) => {
    await page.goto('');
    canvas = new WorkflowCanvas(page);
    dataPanel = new DataInspectionPanel(page);
    await canvas.waitForReady();
  });

  test('should display null values in data preview', async ({ page }) => {
    await canvas.dragNodeToCanvas('input');
    await canvas.selectNodeByIndex(0);
    await uploadTestCsv(page, csvWithNulls);

    await dataPanel.switchToDataTab();

    // Check that null cells are displayed
    const nullCells = page.locator('td').filter({ hasText: /^$/ });
    const nullCount = await nullCells.count();
    expect(nullCount).toBeGreaterThan(0);
  });

  test('should show null count in statistics', async ({ page }) => {
    await canvas.dragNodeToCanvas('input');
    await canvas.selectNodeByIndex(0);
    await uploadTestCsv(page, csvWithNulls);

    await dataPanel.switchToStatsTab();

    // Check statistics for email column (has nulls)
    const emailStats = await dataPanel.getColumnStats('email');
    expect(emailStats).toBeTruthy();
    expect(parseInt(emailStats?.nulls || '0')).toBeGreaterThan(0);
  });

  test('should filter null values with is_null operator', async ({ page }) => {
    await canvas.dragNodeToCanvas('input', { x: 400, y: 100 });
    await canvas.selectNodeByIndex(0);
    await uploadTestCsv(page, csvWithNulls);

    await canvas.dragNodeToCanvas('filter', { x: 400, y: 300 });
    await canvas.dragNodeToCanvas('output', { x: 400, y: 500 });

    await canvas.connectNodes(0, 1);
    await canvas.connectNodes(1, 2);

    // Configure filter for null values
    await canvas.clickNode('Filter');

    const columnSelect = page.locator('select[name="column"]');
    await columnSelect.waitFor({ state: 'visible' });
    await columnSelect.selectOption('email');

    const operatorSelect = page.locator('select[name="operator"]');
    await operatorSelect.selectOption('is_null');

    await page.waitForTimeout(1000);

    // Execute and check
    await canvas.execute();
    await canvas.waitForExecutionComplete();

    await canvas.clickNode('Export');
    await dataPanel.switchToDataTab();

    const rowCount = await dataPanel.getDataRowCount();
    expect(rowCount).toBeGreaterThan(0);
  });

  test('should filter non-null values with is_not_null operator', async ({ page }) => {
    await canvas.dragNodeToCanvas('input', { x: 400, y: 100 });
    await canvas.selectNodeByIndex(0);
    await uploadTestCsv(page, csvWithNulls);

    await canvas.dragNodeToCanvas('filter', { x: 400, y: 300 });
    await canvas.dragNodeToCanvas('output', { x: 400, y: 500 });

    await canvas.connectNodes(0, 1);
    await canvas.connectNodes(1, 2);

    await canvas.clickNode('Filter');

    const columnSelect = page.locator('select[name="column"]');
    await columnSelect.waitFor({ state: 'visible' });
    await columnSelect.selectOption('email');

    const operatorSelect = page.locator('select[name="operator"]');
    await operatorSelect.selectOption('is_not_null');

    await page.waitForTimeout(1000);

    await canvas.execute();
    await canvas.waitForExecutionComplete();

    await canvas.clickNode('Export');
    await dataPanel.switchToDataTab();

    const rowCount = await dataPanel.getDataRowCount();
    expect(rowCount).toBeGreaterThan(0);
  });

  test('should handle null values in aggregation', async ({ page }) => {
    await canvas.dragNodeToCanvas('input', { x: 400, y: 100 });
    await canvas.selectNodeByIndex(0);
    await uploadTestCsv(page, csvWithNulls);

    await canvas.dragNodeToCanvas('aggregate', { x: 400, y: 300 });
    await canvas.dragNodeToCanvas('output', { x: 400, y: 500 });

    await canvas.connectNodes(0, 1);
    await canvas.connectNodes(1, 2);

    // Configure aggregation on column with nulls
    await canvas.clickNode('Aggregate');

    const addAggButton = page.locator('button:has-text("Add")');
    await addAggButton.click();

    const columnSelect = page.locator('select[name="agg-column"]');
    await columnSelect.waitFor({ state: 'visible' });
    await columnSelect.selectOption('age');

    const operationSelect = page.locator('select[name="agg-operation"]');
    await operationSelect.selectOption('avg');

    await page.waitForTimeout(1000);

    await canvas.execute();
    await canvas.waitForExecutionComplete();

    // Should compute average ignoring nulls
    await canvas.clickNode('Export');
    await dataPanel.switchToDataTab();

    await expect(page.locator('table').first()).toBeVisible();
  });

  test('should handle null values in joins', async ({ page }) => {
    await canvas.dragNodeToCanvas('input', { x: 200, y: 100 });
    await canvas.selectNodeByIndex(0);
    await uploadTestCsv(page, csvWithNulls);

    await canvas.dragNodeToCanvas('input', { x: 600, y: 100 });
    await canvas.selectNodeByIndex(1);
    await uploadTestCsv(page, csvWithNulls);

    await canvas.dragNodeToCanvas('combine', { x: 400, y: 300 });
    await canvas.dragNodeToCanvas('output', { x: 400, y: 500 });

    await canvas.connectNodes(0, 2);
    await canvas.connectNodes(1, 2);
    await canvas.connectNodes(2, 3);

    // Configure join
    await canvas.clickNode('Join');

    await page.locator('select[name="joinType"]').selectOption('left');
    await page.locator('select[name="leftColumn"]').selectOption('id');
    await page.locator('select[name="rightColumn"]').selectOption('id');

    await page.waitForTimeout(1000);

    await canvas.execute();
    await canvas.waitForExecutionComplete();

    await canvas.clickNode('Export');
    await dataPanel.switchToDataTab();

    const rowCount = await dataPanel.getDataRowCount();
    expect(rowCount).toBeGreaterThan(0);
  });

  test('should replace null values with clean node', async ({ page }) => {
    await canvas.dragNodeToCanvas('input', { x: 400, y: 100 });
    await canvas.selectNodeByIndex(0);
    await uploadTestCsv(page, csvWithNulls);

    await canvas.dragNodeToCanvas('clean', { x: 400, y: 300 });
    await canvas.dragNodeToCanvas('output', { x: 400, y: 500 });

    await canvas.connectNodes(0, 1);
    await canvas.connectNodes(1, 2);

    // Configure clean node
    await canvas.clickNode('Clean');

    const columnSelect = page.locator('select[name="column"]');
    await columnSelect.waitFor({ state: 'visible' });
    await columnSelect.selectOption('email');

    const operationSelect = page.locator('select[name="operation"]');
    await operationSelect.selectOption('replace_null');

    const newValueInput = page.locator('input[name="newValue"]');
    await newValueInput.fill('unknown');

    await page.waitForTimeout(1000);

    await canvas.execute();
    await canvas.waitForExecutionComplete();

    await canvas.clickNode('Export');
    await dataPanel.switchToStatsTab();

    // Check that nulls were replaced
    const stats = await dataPanel.getColumnStats('email');
    expect(parseInt(stats?.nulls || '0')).toBe(0);
  });

  test('should calculate null percentage correctly', async ({ page }) => {
    await canvas.dragNodeToCanvas('input');
    await canvas.selectNodeByIndex(0);
    await uploadTestCsv(page, csvWithNulls);

    await dataPanel.switchToStatsTab();

    const emailStats = await dataPanel.getColumnStats('email');
    expect(emailStats).toBeTruthy();

    // Verify null percentage is reasonable
    const nullPct = parseFloat(emailStats?.nullPct || '0');
    expect(nullPct).toBeGreaterThan(0);
    expect(nullPct).toBeLessThanOrEqual(100);
  });

  test('should handle all-null columns gracefully', async ({ page }) => {
    await canvas.dragNodeToCanvas('input');
    await canvas.selectNodeByIndex(0);

    // Create CSV with all-null column
    const allNullCsv = {
      name: 'all-null',
      filename: 'all-null.csv',
      content: 'id,name,value\n1,Alice,\n2,Bob,\n3,Carol,'
    };
    
    await uploadTestCsv(page, allNullCsv);

    await dataPanel.switchToStatsTab();

    const valueStats = await dataPanel.getColumnStats('value');
    expect(valueStats).toBeTruthy();
    expect(parseInt(valueStats?.nulls || '0')).toBe(3);
  });
});
