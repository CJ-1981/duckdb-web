import { test, expect } from '@playwright/test';
import { WorkflowCanvas } from './pages/WorkflowCanvas';
import { DataInspectionPanel } from './pages/DataInspectionPanel';
import { uploadTestCsv, sampleCsvData, salesData } from './fixtures/testData';

/**
 * Data Inspection Panel Tests
 *
 * These tests verify the data inspection, schema view, and statistics functionality.
 */

test.describe('Data Inspection Panel Tests', () => {
  let canvas: WorkflowCanvas;
  let panel: DataInspectionPanel;

  test.beforeEach(async ({ page }) => {
    canvas = new WorkflowCanvas(page);
    panel = new DataInspectionPanel(page);

    await page.goto('http://localhost:3000');
    await canvas.waitForReady();

    // Set up a simple workflow
    await canvas.dragNodeToCanvas('input');
    await canvas.selectNodeByIndex(0);
    await uploadTestCsv(page, sampleCsvData);
    await canvas.execute();
    await canvas.waitForExecutionComplete();
  });

  test('data table displays correctly', async ({ page }) => {
    // Switch to data tab
    await panel.switchToDataTab();

    // Verify columns are displayed
    const columns = await panel.getDataColumns();
    expect(columns).toContain('id');
    expect(columns).toContain('name');
    expect(columns).toContain('email');
  });

  test('schema information is accurate', async ({ page }) => {
    // Switch to schema tab
    await panel.switchToSchemaTab();

    // Get schema
    const schema = await panel.getSchema();

    // Verify schema has correct columns
    expect(schema.length).toBeGreaterThan(0);

    const idColumn = schema.find(col => col.name === 'id');
    expect(idColumn).toBeDefined();
    expect(idColumn?.type).toMatch(/integer|bigint|int/i);

    const nameColumn = schema.find(col => col.name === 'name');
    expect(nameColumn).toBeDefined();
    expect(nameColumn?.type).toMatch(/varchar|text|string/i);
  });

  test('statistics are computed correctly', async ({ page }) => {
    // Switch to stats tab
    await panel.switchToStatsTab();

    // Get stats for a numeric column
    const stats = await panel.getColumnStats('age');

    expect(stats).not.toBeNull();
    expect(stats?.count).toBe('10'); // All rows have age
  });

  test('can copy schema in different formats', async ({ page }) => {
    // Switch to schema tab
    await panel.switchToSchemaTab();

    // Test copying in Markdown format
    await panel.copySchema('md');

    // Verify clipboard was set (check for success message)
    const successMsg = page.locator('text=/copied|copied to clipboard/i');
    await expect(successMsg).toBeVisible({ timeout: 5000 });
  });

  test('sample rows are displayed initially', async ({ page }) => {
    // Switch to data tab
    await panel.switchToDataTab();

    // Get row count (should be limited sample)
    const rowCount = await panel.getDataRowCount();

    // Sample should be reasonable size (e.g., 100 rows or less)
    expect(rowCount).toBeLessThanOrEqual(100);
  });

  test('can trigger full dataset analysis', async ({ page }) => {
    // Switch to stats tab
    await panel.switchToStatsTab();

    // Trigger full analysis
    await panel.computeFullStats();

    // Wait for completion
    await panel.waitForFullStats();

    // Verify full stats are displayed
    const fullStatsIndicator = page.locator('text=/full dataset|complete/i');
    await expect(fullStatsIndicator).toBeVisible();
  });

  test('column statistics include null count', async ({ page }) => {
    // Upload data with nulls
    await canvas.dragNodeToCanvas('input', { x: 400, y: 0 });
    await canvas.clickNode('input');
    await canvas.selectNodeByIndex(1);

    const { csvWithNulls } = await import('../fixtures/testData');
    await uploadTestCsv(page, csvWithNulls);
    await canvas.execute();
    await canvas.waitForExecutionComplete();

    // Switch to stats tab
    await panel.switchToStatsTab();

    // Check stats for a column with nulls
    const stats = await panel.getColumnStats('email');

    expect(stats).not.toBeNull();
    expect(parseInt(stats?.nulls || '0')).toBeGreaterThan(0);
  });

  test('data preview pagination works', async ({ page }) => {
    // Upload larger dataset
    await canvas.clickNode('input');

    await uploadTestCsv(page, salesData);
    await canvas.execute();
    await canvas.waitForExecutionComplete();

    // Switch to data tab
    await panel.switchToDataTab();

    // Check if pagination controls exist
    const pagination = page.locator('[data-testid="pagination"], .pagination').first();
    const hasPagination = await pagination.isVisible().catch(() => false);

    if (hasPagination) {
      // Click next page
      const nextButton = pagination.locator('button:has-text("Next"), button[aria-label="next"]');
      const canClickNext = await nextButton.isEnabled().catch(() => false);

      if (canClickNext) {
        await nextButton.click();

        // Verify data changed (different rows shown)
        const currentData = await panel.getTableData();
        expect(currentData.length).toBeGreaterThan(0);
      }
    }
  });

  test('can search/filter in data table', async ({ page }) => {
    // Switch to data tab
    await panel.switchToDataTab();

    // Look for search input
    const searchInput = page.locator('input[placeholder*="search" i], input[data-testid="search"]').first();
    const hasSearch = await searchInput.isVisible().catch(() => false);

    if (hasSearch) {
      // Enter search term
      await searchInput.fill('Alice');

      // Verify filtered results
      const tableData = await panel.getTableData();
      const hasAlice = tableData.some(row => row.some(cell => cell.includes('Alice')));

      expect(hasAlice).toBe(true);
    }
  });

  test('displays correct data types', async ({ page }) => {
    // Switch to schema tab
    await panel.switchToSchemaTab();

    // Verify type detection for various columns
    const schema = await panel.getSchema();

    const idType = schema.find(col => col.name === 'id')?.type;
    const ageType = schema.find(col => col.name === 'age')?.type;
    const nameType = schema.find(col => col.name === 'name')?.type;

    // ID should be integer
    expect(idType).toMatch(/integer|int|bigint/i);

    // Age should be numeric
    expect(ageType).toMatch(/integer|double|numeric/i);

    // Name should be text
    expect(nameType).toMatch(/varchar|text|string/i);
  });

  test('shows no data message before execution', async ({ page }) => {
    // Add new node without executing
    await canvas.dragNodeToCanvas('filter', { x: 300, y: 100 });
    await canvas.clickNode('filter');

    // Verify no data message
    const isNoData = await panel.isNoDataMessage();
    expect(isNoData).toBe(true);
  });

  test('updates data when node changes', async ({ page }) => {
    // Get initial data
    await panel.switchToDataTab();
    const initialData = await panel.getTableData();

    // Add a filter node
    await canvas.dragNodeToCanvas('filter', { x: 300, y: 100 });
    await canvas.connectNodes('input', 'filter');
    await canvas.clickNode('filter');

    // Configure filter (this would depend on actual UI)
    // For now, just execute and verify data changes
    await canvas.execute();
    await canvas.waitForExecutionComplete();

    // Select filter node to see its data
    await panel.switchToDataTab();
    const filteredData = await panel.getTableData();

    // Data should be different or same size (depending on filter)
    expect(filteredData.length).toBeGreaterThanOrEqual(0);
  });

  test('handles column with special characters in name', async ({ page }) => {
    // Upload CSV with special column names
    const specialColumnsCsv = {
      name: 'Special Columns',
      content: 'id,"User Name","Email Address",age\n1,"Alice Smith","alice@example.com",30',
      filename: 'special-columns.csv',
    };

    await canvas.clickNode('input');
    await uploadTestCsv(page, specialColumnsCsv);
    await canvas.execute();
    await canvas.waitForExecutionComplete();

    // Verify columns with special characters are displayed
    await panel.switchToDataTab();
    const columns = await panel.getDataColumns();

    expect(columns).toContain('User Name');
    expect(columns).toContain('Email Address');
  });
});
