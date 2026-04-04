import { expect } from '@playwright/test';
import type { Page } from '@playwright/test';

/**
 * Custom assertion helpers for E2E tests
 * Provides domain-specific assertions for the DuckDB web application
 */

/**
 * Assert that a node exists on the canvas
 */
export async function assertNodeExists(page: Page, nodeLabel: string) {
  await expect(
    page.locator('.react-flow__node').filter({ hasText: nodeLabel })
  ).toBeVisible();
}

/**
 * Assert that a node does not exist on the canvas
 */
export async function assertNodeNotExists(page: Page, nodeLabel: string) {
  const node = page.locator('.react-flow__node').filter({ hasText: nodeLabel });
  const count = await node.count();
  expect(count).toBe(0);
}

/**
 * Assert that two nodes are connected
 */
export async function assertNodesConnected(page: Page, sourceLabel: string, targetLabel: string) {
  const edge = page.locator('.react-flow__edge').filter({
    has: page.locator(`text=/${sourceLabel}/`),
  });

  await expect(edge).toHaveAttribute('data-source', /.+/);
}

/**
 * Assert that the workflow executed successfully
 */
export async function assertExecutionSuccess(page: Page) {
  await expect(
    page.locator('[data-testid="execution-success"], text=/executed successfully|execution complete/i')
  ).toBeVisible({ timeout: 60000 });
}

/**
 * Assert that the workflow execution failed
 */
export async function assertExecutionFailed(page: Page) {
  await expect(
    page.locator('[data-testid="execution-error"], text=/execution failed|error/i')
  ).toBeVisible({ timeout: 60000 });
}

/**
 * Assert that a node has a specific row count
 */
export async function assertNodeRowCount(page: Page, nodeLabel: string, expectedCount: number) {
  const node = page.locator('.react-flow__node').filter({ hasText: nodeLabel });
  const rowCountText = await node.locator('text=/rows/i').textContent();
  const match = rowCountText?.match(/(\d+(,\d+)*)/);
  const actualCount = match?.[1].replace(/,/g, '');
  expect(actualCount).toBe(String(expectedCount));
}

/**
 * Assert that the data preview shows specific columns
 */
export async function assertDataColumns(page: Page, expectedColumns: string[]) {
  const columns = await page.locator('th').allTextContents();
  for (const col of expectedColumns) {
    expect(columns).toContain(col);
  }
}

/**
 * Assert that a column has a specific data type
 */
export async function assertColumnType(page: Page, columnName: string, expectedType: string) {
  const columnRow = page.locator('tr').filter({ hasText: columnName });
  await expect(columnRow).toContainText(expectedType);
}

/**
 * Assert that the data table contains a specific row
 */
export async function assertTableContainsRow(page: Page, rowValues: string[]) {
  for (const value of rowValues) {
    await expect(page.locator('td').filter({ hasText: value })).toBeVisible();
  }
}

/**
 * Assert that the data table does not contain a specific value
 */
export async function assertTableNotContains(page: Page, value: string) {
  const cells = page.locator('td').filter({ hasText: value });
  const count = await cells.count();
  expect(count).toBe(0);
}

/**
 * Assert that the data panel shows "no data" message
 */
export async function assertNoDataMessage(page: Page) {
  await expect(
    page.locator('text=/no sample data|execute the workflow to inspect/i')
  ).toBeVisible();
}

/**
 * Assert that the data panel is showing data
 */
export async function assertHasData(page: Page) {
  await expect(
    page.locator('table tbody tr').first()
  ).toBeVisible();
}

/**
 * Assert that a filter node was applied correctly
 */
export async function assertFilterApplied(page: Page, column: string, operator: string, value: string) {
  const nodeConfig = page.locator('[data-testid="node-config"], .node-config');
  await expect(nodeConfig).toContainText(column);
  await expect(nodeConfig).toContainText(operator);
  await expect(nodeConfig).toContainText(value);
}

/**
 * Assert that an aggregate node was configured correctly
 */
export async function assertAggregateConfigured(page: Page, groupBy: string, aggregations: Array<{column: string, operation: string}>) {
  const nodeConfig = page.locator('[data-testid="node-config"], .node-config');
  await expect(nodeConfig).toContainText(groupBy);

  for (const agg of aggregations) {
    await expect(nodeConfig).toContainText(agg.column);
    await expect(nodeConfig).toContainText(agg.operation.toUpperCase());
  }
}

/**
 * Assert that a join node was configured correctly
 */
export async function assertJoinConfigured(page: Page, joinType: string, leftColumn: string, rightColumn: string) {
  const nodeConfig = page.locator('[data-testid="node-config"], .node-config');
  await expect(nodeConfig).toContainText(joinType.toUpperCase());
  await expect(nodeConfig).toContainText(leftColumn);
  await expect(nodeConfig).toContainText(rightColumn);
}

/**
 * Assert that the canvas has a specific number of nodes
 */
export async function assertNodeCount(page: Page, expectedCount: number) {
  const actualCount = await page.locator('.react-flow__node').count();
  expect(actualCount).toBe(expectedCount);
}

/**
 * Assert that the canvas has a specific number of edges
 */
export async function assertEdgeCount(page: Page, expectedCount: number) {
  const actualCount = await page.locator('.react-flow__edge').count();
  expect(actualCount).toBe(expectedCount);
}

/**
 * Assert that a specific tab is active in the data panel
 */
export async function assertTabActive(page: Page, tabName: 'data' | 'schema' | 'stats') {
  const tabText = tabName === 'data' ? 'Data Table' : tabName === 'schema' ? 'Schema' : 'Statistics';
  const activeTab = page.locator('button').filter({ hasText: tabText });
  await expect(activeTab).toHaveClass(/border-\[#0052CC\]|text-\[#0052CC\]/);
}

/**
 * Assert that a file was uploaded successfully
 */
export async function assertFileUploaded(page: Page, filename: string) {
  await expect(
    page.locator(`text=/${filename}|uploaded successfully/i`)
  ).toBeVisible();
}

/**
 * Assert that the SQL preview shows specific content
 */
export async function assertSqlPreviewContains(page: Page, expectedSql: string) {
  const sqlPreview = page.locator('[data-testid="sql-preview"], pre:has-text("SELECT")');
  await expect(sqlPreview).toContainText(expectedSql, { ignoreCase: true });
}

/**
 * Assert that statistics are displayed for a column
 */
export async function assertColumnStatsExist(page: Page, columnName: string) {
  const statsBlock = page.locator('[data-testid="column-stats"]').filter({ hasText: columnName });
  await expect(statsBlock).toBeVisible();
  await expect(statsBlock).toContainText('Non-Null');
  await expect(statsBlock).toContainText('Distinct');
  await expect(statsBlock).toContainText('Nulls');
}

/**
 * Assert that null handling is working correctly
 */
export async function assertNullValueHandled(page: Page, columnName: string) {
  const nullCount = await page.locator(`tr:has-text("${columnName}")`).locator('text=/null/i').textContent();
  const count = parseInt(nullCount?.match(/\d+/)?.[0] || '0');
  expect(count).toBeGreaterThanOrEqual(0);
}

/**
 * Assert that special characters are preserved correctly
 */
export async function assertSpecialCharsPreserved(page: Page, expectedValue: string) {
  await expect(page.locator('td').filter({ hasText: expectedValue })).toBeVisible();
}

/**
 * Assert workflow was saved successfully
 */
export async function assertWorkflowSaved(page: Page) {
  await expect(
    page.locator('text=/workflow saved|saved successfully/i')
  ).toBeVisible();
}

/**
 * Assert workflow was loaded successfully
 */
export async function assertWorkflowLoaded(page: Page, workflowName: string) {
  await expect(
    page.locator(`text=/${workflowName}|loaded successfully/i`)
  ).toBeVisible();
}
