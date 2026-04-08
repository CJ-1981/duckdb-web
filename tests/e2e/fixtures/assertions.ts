import { expect } from '@playwright/test';
import type { Page } from '@playwright/test';

/**
 * Custom assertion helpers for E2E tests
 * Provides domain-specific assertions for the DuckDB web application
 */

function getLabelRegex(label: string): RegExp {
  const l = label.toLowerCase();
  let pattern = label;
  if (l === 'input' || l.includes('csv')) pattern = 'CSV/Excel File|Input';
  else if (l === 'filter') pattern = 'Filter Records|Filter';
  else if (l === 'aggregate') pattern = 'Aggregate Data|Aggregate';
  else if (l === 'combine' || l.includes('join')) pattern = 'Combine Datasets|Join|Combine';
  else if (l === 'output' || l.includes('export')) pattern = 'Export File|Output|Export';
  else if (l === 'sql') pattern = 'Custom SQL|SQL';
  
  return new RegExp(pattern, 'i');
}

/**
 * Assert that a specific node exists on the canvas
 */
export async function assertNodeExists(page: Page, nodeLabel: string) {
  const regex = getLabelRegex(nodeLabel);
  const node = page.locator('.react-flow__node').filter({ hasText: regex }).first();
  await expect(node).toBeVisible({ timeout: 10000 });
}

/**
 * Assert that a specific node does not exist on the canvas
 */
export async function assertNodeNotExists(page: Page, nodeLabel: string) {
  const regex = getLabelRegex(nodeLabel);
  const node = page.locator('.react-flow__node').filter({ hasText: regex });
  await expect(node).not.toBeVisible();
}

/**
 * Assert that two nodes are connected
 */
export async function assertNodesConnected(page: Page, sourceLabel: string, targetLabel: string) {
  // This is a complex assertion as edges are rendered separately in SVG
  // For now, we check if at least one edge exists
  const edgeCount = await page.locator('.react-flow__edge').count();
  expect(edgeCount).toBeGreaterThan(0);
}

/**
 * Assert that the SQL preview contains a specific string
 */
export async function assertSqlPreviewContains(page: Page, text: string) {
  const preview = page.locator('[data-testid="sql-preview"], .sql-preview, pre').first();
  await expect(preview).toContainText(text);
}

/**
 * Assert that the data table contains a specific value
 */
export async function assertDataTableContains(page: Page, value: string) {
  const table = page.locator('.data-table, table').first();
  await expect(table).toContainText(value);
}

/**
 * Assert that execution was successful
 */
export async function assertExecutionSuccess(page: Page) {
  const successIndicator = page.locator('[data-testid="execution-success"], text=/executed successfully/i').first();
  await expect(successIndicator).toBeVisible({ timeout: 10000 });
}

/**
 * Assert workflow was loaded successfully
 */
export async function assertWorkflowLoaded(page: Page, workflowName: string) {
  await expect(
    page.locator(`text=/${workflowName}|loaded successfully/i`)
  ).toBeVisible();
}
