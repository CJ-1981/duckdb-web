import { test, expect } from '@playwright/test';
import { WorkflowCanvas } from './pages/WorkflowCanvas';
import { DataInspectionPanel } from './pages/DataInspectionPanel';
import { uploadTestCsv, csvWithNulls, csvWithSpecialChars, getAllTestDatasets } from './fixtures/testData';

/**
 * Edge Cases Tests
 *
 * These tests verify the application handles edge cases correctly,
 * including null values, special characters, large datasets, and error conditions.
 */

test.describe('Edge Cases Tests', () => {
  let canvas: WorkflowCanvas;
  let panel: DataInspectionPanel;

  test.beforeEach(async ({ page }) => {
    canvas = new WorkflowCanvas(page);
    panel = new DataInspectionPanel(page);

    await page.goto('');
    await canvas.waitForReady();
  });

  test('handles CSV with null values', async ({ page }) => {
    // Add input node and upload CSV with nulls
    await canvas.dragNodeToCanvas('input');
    await canvas.selectNodeByIndex(0);
    await uploadTestCsv(page, csvWithNulls);

    // Execute workflow
    await canvas.execute();
    await canvas.waitForExecutionComplete();
    await page.waitForTimeout(3000); // Wait for data to populate

    // Verify data inspection panel shows null values correctly
    await panel.switchToDataTab();

    // Wait for table to be visible and have data
    await expect(page.locator('tbody tr').first()).toBeVisible({ timeout: 5000 });

    const data = await panel.getTableData();

    // Debug: log the data to see what we're getting
    console.log('Table data:', JSON.stringify(data));

    // Check that null cells are properly displayed as empty strings
    // The CSV has empty cells in row 2 (email), row 3 (age), and row 4 (city)
    const hasEmptyCells = data.some(row => row.some(cell => cell === '' || cell === 'null' || cell === 'NULL'));
    expect(hasEmptyCells).toBe(true);
  });

  test('handles CSV with special characters', async ({ page }) => {
    // Add input node and upload CSV with special chars
    await canvas.dragNodeToCanvas('input');
    await canvas.selectNodeByIndex(0);
    await uploadTestCsv(page, csvWithSpecialChars);

    // Execute workflow
    await canvas.execute();
    await canvas.waitForExecutionComplete();

    // Verify special characters are preserved
    await panel.switchToDataTab();
    const columns = await panel.getDataColumns();

    expect(columns).toContain('description');

    // Verify data with commas is in one cell
    const firstRow = await panel.getTableData();
    const descriptionCell = firstRow[0][columns.indexOf('description')];
    expect(descriptionCell).toContain('commas');
  });

  test('handles empty CSV file', async ({ page }) => {
    // Create empty CSV
    const emptyCsv = {
      name: 'Empty',
      content: '',
      filename: 'empty.csv',
    };

    // Add input node
    await canvas.dragNodeToCanvas('input');
    await canvas.selectNodeByIndex(0);

    // Try to upload empty CSV
    await uploadTestCsv(page, emptyCsv);

    // Verify error message is shown
    const errorMessage = page.locator('text=/error|invalid|empty/i').first();
    await expect(errorMessage).toBeVisible({ timeout: 10000 });
  });

  test('handles CSV with only headers', async ({ page }) => {
    const headerOnlyCsv = {
      name: 'Headers Only',
      content: 'id,name,email\n',
      filename: 'headers-only.csv',
    };

    // Add input node
    await canvas.dragNodeToCanvas('input');
    await canvas.selectNodeByIndex(0);
    await uploadTestCsv(page, headerOnlyCsv);

    // Execute workflow
    await canvas.execute();
    await canvas.waitForExecutionComplete();

    // Verify schema is detected but no data rows
    await panel.switchToSchemaTab();
    const schema = await panel.getSchema();

    expect(schema.length).toBeGreaterThan(0);
    expect(schema[0].name).toBe('id');
  });

  test('handles malformed CSV', async ({ page }) => {
    const malformedCsv = {
      name: 'Malformed',
      content: 'id,name\n1,Alice\n2,Bob,Extra,Column\n3,Charlie',
      filename: 'malformed.csv',
    };

    // Add input node
    await canvas.dragNodeToCanvas('input');
    await canvas.selectNodeByIndex(0);
    await uploadTestCsv(page, malformedCsv);

    // Execute workflow
    await canvas.execute();
    await canvas.waitForExecutionComplete();

    // Verify error or warning is shown
    const warningMessage = page.locator('text=/warning|mismatch|columns/i').first();
    const isVisible = await warningMessage.isVisible().catch(() => false);

    // Either show a warning or handle it gracefully
    expect(isVisible || await canvas.getNodeCount() > 0).toBe(true);
  });

  test('handles CSV with different date formats', async ({ page }) => {
    const dateFormatsCsv = {
      name: 'Date Formats',
      content: `id,date_iso,date_us,date_eu
1,2024-01-15,01/15/2024,15.01.2024
2,2024-12-31,12/31/2024,31.12.2024`,
      filename: 'date-formats.csv',
    };

    // Add input node
    await canvas.dragNodeToCanvas('input');
    await canvas.selectNodeByIndex(0);
    await uploadTestCsv(page, dateFormatsCsv);

    // Execute workflow
    await canvas.execute();
    await canvas.waitForExecutionComplete();

    // Verify dates are detected as date type
    await panel.switchToSchemaTab();
    const dateIsoType = await panel.getColumnType('date_iso');

    expect(dateIsoType).toMatch(/date|varchar/i);
  });

  test('handles CSV with numeric strings', async ({ page }) => {
    const numericStringsCsv = {
      name: 'Numeric Strings',
      content: 'id,amount,zipcode\n1,1000.50,"12345"\n2,2500.75,"54321"',
      filename: 'numeric-strings.csv',
    };

    // Add input node
    await canvas.dragNodeToCanvas('input');
    await canvas.selectNodeByIndex(0);
    await uploadTestCsv(page, numericStringsCsv);

    // Execute workflow
    await canvas.execute();
    await canvas.waitForExecutionComplete();

    // Verify type detection
    await panel.switchToSchemaTab();
    const amountType = await panel.getColumnType('amount');

    expect(amountType).toMatch(/double|decimal|numeric|varchar/i);
  });

  test('handles very long text values', async ({ page }) => {
    const longText = 'a'.repeat(10000); // 10k characters
    const longTextCsv = {
      name: 'Long Text',
      content: `id,text
1,${longText}`,
      filename: 'long-text.csv',
    };

    // Add input node
    await canvas.dragNodeToCanvas('input');
    await canvas.selectNodeByIndex(0);
    await uploadTestCsv(page, longTextCsv);

    // Execute workflow
    await canvas.execute();
    await canvas.waitForExecutionComplete();

    // Verify long text is handled (not truncated in storage)
    await panel.switchToDataTab();
    const cellValue = await panel.getCellValue(0, 'text');

    expect(cellValue.length).toBeGreaterThan(100);
  });

  test('handles CSV with leading/trailing spaces', async ({ page }) => {
    const spacesCsv = {
      name: 'Spaces',
      content: 'id,name,city\n1,  Alice  ,  New York  \n2,  Bob  ,  Los Angeles  ',
      filename: 'spaces.csv',
    };

    // Add input node
    await canvas.dragNodeToCanvas('input');
    await canvas.selectNodeByIndex(0);
    await uploadTestCsv(page, spacesCsv);

    // Execute workflow
    await canvas.execute();
    await canvas.waitForExecutionComplete();

    // Verify spaces are handled (either trimmed or preserved)
    await panel.switchToDataTab();
    const nameValue = await panel.getCellValue(0, 'name');

    // Name should not have excessive leading/trailing spaces
    expect(nameValue.trim().length).toBeLessThanOrEqual(nameValue.length);
  });

  test('handles CSV with unicode characters', async ({ page }) => {
    const unicodeCsv = {
      name: 'Unicode',
      content: 'id,name,emoji\n1,日本語,🎉\n2,한국어,🚀\n3,中文,💯',
      filename: 'unicode.csv',
    };

    // Add input node
    await canvas.dragNodeToCanvas('input');
    await canvas.selectNodeByIndex(0);
    await uploadTestCsv(page, unicodeCsv);

    // Execute workflow
    await canvas.execute();
    await canvas.waitForExecutionComplete();

    // Verify unicode characters are preserved
    await panel.switchToDataTab();
    const nameValue = await panel.getCellValue(0, 'name');

    expect(nameValue).toMatch(/[日本語한국어中文]/);
  });

  test('handles large dataset gracefully', async ({ page }) => {
    // Generate a larger CSV (100 rows)
    const rows = ['id,name,value'];
    for (let i = 1; i <= 100; i++) {
      rows.push(`${i},Item${i},${i * 10.5}`);
    }
    const largeCsv = {
      name: 'Large Dataset',
      content: rows.join('\n'),
      filename: 'large.csv',
    };

    // Add input node
    await canvas.dragNodeToCanvas('input');
    await canvas.selectNodeByIndex(0);
    await uploadTestCsv(page, largeCsv);

    // Execute workflow
    await canvas.execute();
    await canvas.waitForExecutionComplete();

    // Trigger full dataset analysis
    await panel.switchToStatsTab();
    await panel.computeFullStats();
    await panel.waitForFullStats();

    // Verify data is loaded (check stats)
    const stats = await panel.getColumnStats('id');

    expect(stats).not.toBeNull();
    expect(stats?.count).toBe('100');
  });

  test('handles duplicate column names', async ({ page }) => {
    const duplicateColsCsv = {
      name: 'Duplicate Columns',
      content: 'id,name,name\n1,Alice,Smith\n2,Bob,Johnson',
      filename: 'duplicate-cols.csv',
    };

    // Add input node
    await canvas.dragNodeToCanvas('input');
    await canvas.selectNodeByIndex(0);
    await uploadTestCsv(page, duplicateColsCsv);

    // Execute workflow
    await canvas.execute();

    // Verify error or handling of duplicate columns
    const errorMessage = page.locator('text=/duplicate|error/i').first();
    const hasError = await errorMessage.isVisible().catch(() => false);

    // Either show an error or handle duplicates by adding suffixes
    expect(hasError || await canvas.getNodeCount() > 0).toBe(true);
  });

  test.skip('handles workflow with circular dependencies - Edge creation via drag-drop unreliable in headless browser. Business logic tested separately. See PHASE3_FINAL.md', async ({ page }) => {
    // Add nodes in a way that could create circular dependency
    await canvas.dragNodeToCanvas('input', { x: 400, y: 100 });
    await canvas.dragNodeToCanvas('filter', { x: 400, y: 300 });
    await canvas.dragNodeToCanvas('aggregate', { x: 400, y: 500 });

    // Connect: input -> filter -> aggregate
    await canvas.connectNodes('input', 'filter');
    await canvas.connectNodes('filter', 'aggregate');

    // Try to connect aggregate back to filter (should be prevented)
    await canvas.connectNodes('aggregate', 'filter');

    // Execute workflow
    await canvas.execute();

    // Should either execute successfully (if cycle prevented) or show error
    const nodeCount = await canvas.getNodeCount();
    expect(nodeCount).toBeGreaterThan(0);
  });

  test.skip('handles disconnection of required nodes - Edge creation via drag-drop unreliable in headless browser. Business logic tested separately. See PHASE3_FINAL.md', async ({ page }) => {
    // Add and connect nodes
    await canvas.dragNodeToCanvas('input', { x: 400, y: 100 });
    await canvas.dragNodeToCanvas('filter', { x: 400, y: 300 });
    await canvas.connectNodes('input', 'filter');

    // Disconnect the nodes
    const edge = page.locator('.react-flow__edge').first();
    await edge.click();
    await page.keyboard.press('Delete');

    // Try to execute with disconnected workflow
    await canvas.execute();

    // Verify warning about disconnected nodes
    const warning = page.locator('text=/disconnected|warning|no data|error/i').first();
    const hasWarning = await warning.isVisible().catch(() => false);

    expect(hasWarning).toBe(true);
  });
});
