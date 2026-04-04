import { Page } from '@playwright/test';
import { Node, Edge } from '@xyflow/react';

/**
 * Workflow fixtures for E2E tests
 * Provides pre-configured workflows for testing
 */

export interface WorkflowDefinition {
  name: string;
  description: string;
  nodes: Node[];
  edges: Edge[];
}

/**
 * Simple linear workflow: Input -> Filter -> Output
 */
export const simpleFilterWorkflow: WorkflowDefinition = {
  name: 'Simple Filter Workflow',
  description: 'Input node connected to a filter node, then to an output node',
  nodes: [
    {
      id: 'input-1',
      type: 'input',
      position: { x: 100, y: 100 },
      data: { label: 'Users Data', subtype: 'csv' },
    },
    {
      id: 'filter-1',
      type: 'default',
      position: { x: 400, y: 100 },
      data: {
        label: 'Filter Age > 25',
        subtype: 'filter',
        config: {
          column: 'age',
          operator: '>',
          value: '25',
        },
      },
    },
    {
      id: 'output-1',
      type: 'output',
      position: { x: 700, y: 100 },
      data: { label: 'Filtered Users', subtype: 'csv' },
    },
  ],
  edges: [
    { id: 'e1', source: 'input-1', target: 'filter-1', animated: true },
    { id: 'e2', source: 'filter-1', target: 'output-1', animated: true },
  ],
};

/**
 * Aggregate workflow: Input -> Aggregate -> Output
 */
export const aggregateWorkflow: WorkflowDefinition = {
  name: 'Aggregate Workflow',
  description: 'Input node connected to an aggregate node, then to an output node',
  nodes: [
    {
      id: 'input-1',
      type: 'input',
      position: { x: 100, y: 100 },
      data: { label: 'Sales Data', subtype: 'csv' },
    },
    {
      id: 'aggregate-1',
      type: 'default',
      position: { x: 400, y: 100 },
      data: {
        label: 'Sum Sales by Region',
        subtype: 'aggregate',
        config: {
          groupBy: 'region',
          aggregations: [
            { column: 'sales', operation: 'sum', alias: 'total_sales' },
          ],
        },
      },
    },
    {
      id: 'output-1',
      type: 'output',
      position: { x: 700, y: 100 },
      data: { label: 'Regional Sales', subtype: 'csv' },
    },
  ],
  edges: [
    { id: 'e1', source: 'input-1', target: 'aggregate-1', animated: true },
    { id: 'e2', source: 'aggregate-1', target: 'output-1', animated: true },
  ],
};

/**
 * Join workflow: Input1 -> Join <- Input2 -> Output
 */
export const joinWorkflow: WorkflowDefinition = {
  name: 'Join Workflow',
  description: 'Two input nodes joined together, then to an output node',
  nodes: [
    {
      id: 'input-1',
      type: 'input',
      position: { x: 100, y: 50 },
      data: { label: 'Users', subtype: 'csv' },
    },
    {
      id: 'input-2',
      type: 'input',
      position: { x: 100, y: 250 },
      data: { label: 'Orders', subtype: 'csv' },
    },
    {
      id: 'join-1',
      type: 'default',
      position: { x: 400, y: 150 },
      data: {
        label: 'Join Users-Orders',
        subtype: 'combine',
        config: {
          joinType: 'inner',
          leftColumn: 'id',
          rightColumn: 'user_id',
        },
      },
    },
    {
      id: 'output-1',
      type: 'output',
      position: { x: 700, y: 150 },
      data: { label: 'User Orders', subtype: 'csv' },
    },
  ],
  edges: [
    { id: 'e1', source: 'input-1', target: 'join-1', animated: true },
    { id: 'e2', source: 'input-2', target: 'join-1', animated: true },
    { id: 'e3', source: 'join-1', target: 'output-1', animated: true },
  ],
};

/**
 * Multi-step workflow: Input -> Filter -> Aggregate -> Sort -> Output
 */
export const multiStepWorkflow: WorkflowDefinition = {
  name: 'Multi-Step Workflow',
  description: 'Complex workflow with multiple transformations',
  nodes: [
    {
      id: 'input-1',
      type: 'input',
      position: { x: 100, y: 100 },
      data: { label: 'Sales Data', subtype: 'csv' },
    },
    {
      id: 'filter-1',
      type: 'default',
      position: { x: 300, y: 100 },
      data: {
        label: 'Filter North Region',
        subtype: 'filter',
        config: {
          column: 'region',
          operator: '==',
          value: 'North',
        },
      },
    },
    {
      id: 'aggregate-1',
      type: 'default',
      position: { x: 500, y: 100 },
      data: {
        label: 'Sum by Product',
        subtype: 'aggregate',
        config: {
          groupBy: 'product',
          aggregations: [
            { column: 'sales', operation: 'sum', alias: 'total_sales' },
          ],
        },
      },
    },
    {
      id: 'sort-1',
      type: 'default',
      position: { x: 700, y: 100 },
      data: {
        label: 'Sort by Sales',
        subtype: 'sort',
        config: {
          column: 'total_sales',
          direction: 'desc',
        },
      },
    },
    {
      id: 'output-1',
      type: 'output',
      position: { x: 900, y: 100 },
      data: { label: 'Top Products', subtype: 'csv' },
    },
  ],
  edges: [
    { id: 'e1', source: 'input-1', target: 'filter-1', animated: true },
    { id: 'e2', source: 'filter-1', target: 'aggregate-1', animated: true },
    { id: 'e3', source: 'aggregate-1', target: 'sort-1', animated: true },
    { id: 'e4', source: 'sort-1', target: 'output-1', animated: true },
  ],
};

/**
 * Load a workflow onto the canvas
 */
export async function loadWorkflow(page: Page, workflow: WorkflowDefinition) {
  // Set the workflow in the page's state
  await page.evaluate((wf) => {
    // @ts-ignore - accessing internal state
    window.setWorkflow?.(wf.nodes, wf.edges);
  }, workflow);

  // Wait for nodes to appear on canvas
  const nodeCount = await page.locator('.react-flow__node').count();
  if (nodeCount === 0) {
    throw new Error('Failed to load workflow - no nodes found on canvas');
  }
}

/**
 * Get all workflow definitions
 */
export function getAllWorkflows(): WorkflowDefinition[] {
  return [
    simpleFilterWorkflow,
    aggregateWorkflow,
    joinWorkflow,
    multiStepWorkflow,
  ];
}

/**
 * Get workflow by name
 */
export function getWorkflow(name: string): WorkflowDefinition | undefined {
  return getAllWorkflows().find(wf => wf.name === name);
}
