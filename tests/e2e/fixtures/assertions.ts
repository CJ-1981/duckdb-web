import { expect } from '@playwright/test';
import type { Page } from '@playwright/test';

/**
 * Custom assertion helpers for E2E tests
 * Provides domain-specific assertions for the DuckDB web application
 */

function escapeRegExp(s: string): string {
  return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function getLabelRegex(label: string): RegExp {
  const l = label.toLowerCase();
  let pattern = escapeRegExp(label);
  if (l === 'input' || l.includes('csv')) pattern = '(CSV/Excel File|Input)';
  else if (l === 'filter') pattern = '(Filter Records|Filter)';
  else if (l === 'aggregate') pattern = '(Aggregate Data|Aggregate)';
  else if (l === 'combine' || l.includes('join')) pattern = '(Combine Datasets|Join|Combine)';
  else if (l === 'output' || l.includes('export')) pattern = '(Export File|Output|Export)';
  else if (l === 'sql') pattern = '(Custom SQL|SQL)';
  
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
  await expect(node).toHaveCount(0);
}

/**
 * Assert that two nodes are connected
 */
export async function assertNodesConnected(page: Page, sourceLabel: string, targetLabel: string) {
  const sourceRegex = getLabelRegex(sourceLabel);
  const targetRegex = getLabelRegex(targetLabel);
  
  // Get source and target node IDs
  const sourceNode = page.locator('.react-flow__node').filter({ hasText: sourceRegex }).first();
  const targetNode = page.locator('.react-flow__node').filter({ hasText: targetRegex }).first();
  
  await expect(sourceNode).toBeVisible();
  await expect(targetNode).toBeVisible();
  
  const sourceId = await sourceNode.getAttribute('data-id');
  const targetId = await targetNode.getAttribute('data-id');
  
  if (!sourceId || !targetId) {
    throw new Error(`Could not find node IDs for ${sourceLabel} or ${targetLabel}`);
  }
  
  // Use React Flow API to check for edges between the nodes
  const edgeExists = await page.evaluate(
    ({ srcId, tgtId }) => {
      // Access the React Flow instance if available
      const rfContainer = document.querySelector('.react-flow');
      if (!rfContainer) return false;
      
      // Look for edge elements in DOM
      const edges = document.querySelectorAll('.react-flow__edge, [data-testid^="rf__edge-"]');
      for (const edge of edges) {
        const source = edge.getAttribute('data-source') || edge.getAttribute('aria-label')?.split('to')[0]?.trim();
        const target = edge.getAttribute('data-target') || edge.getAttribute('aria-label')?.split('to')[1]?.trim();
        
        if ((source === srcId && target === tgtId) || 
            (source === tgtId && target === srcId)) {
          return true;
        }
      }
      return false;
    },
    { srcId: sourceId, tgtId: targetId }
  );
  
  expect(edgeExists).toBe(true);
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

/**
 * Assert that a filter has been applied
 */
export async function assertFilterApplied(page: Page) {
  const filterNode = page.locator('.react-flow__node').filter({ hasText: /filter/i }).first();
  await expect(filterNode).toBeVisible();
}

/**
 * Assert that a join has been configured
 */
export async function assertJoinConfigured(page: Page) {
  const joinNode = page.locator('.react-flow__node').filter({ hasText: /join|combine/i }).first();
  await expect(joinNode).toBeVisible();
}

/**
 * Assert that the canvas has a specific number of nodes
 */
export async function assertNodeCount(page: Page, expectedCount: number) {
  const nodes = page.locator('.react-flow__node');
  await expect(nodes).toHaveCount(expectedCount);
}
