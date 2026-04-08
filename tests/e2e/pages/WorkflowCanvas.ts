import { Page, Locator, expect } from '@playwright/test';

/**
 * Node type mapping for palette labels and technical subtypes
 */
const NODE_TYPE_MAP: Record<string, { label: string; subtype: string }> = {
  'input': { label: 'CSV/Excel File', subtype: 'csv' },
  'csv': { label: 'CSV/Excel File', subtype: 'csv' },
  'filter': { label: 'Filter Records', subtype: 'filter' },
  'output': { label: 'Export File', subtype: 'export' },
  'export': { label: 'Export File', subtype: 'export' },
  'aggregate': { label: 'Aggregate Data', subtype: 'aggregate' },
  'combine': { label: 'Combine Datasets', subtype: 'combine' },
  'join': { label: 'Combine Datasets', subtype: 'combine' },
  'clean': { label: 'Clean Data', subtype: 'clean' },
  'sort': { label: 'Sort Records', subtype: 'sort' },
  'limit': { label: 'Limit Rows', subtype: 'limit' },
  'select': { label: 'Select Columns', subtype: 'select' },
  'computed': { label: 'Add Column', subtype: 'computed' },
  'rename': { label: 'Rename Columns', subtype: 'rename' },
  'distinct': { label: 'Remove Duplicates', subtype: 'distinct' },
  'case_when': { label: 'Logic', subtype: 'case_when' },
  'window': { label: 'Window Function', subtype: 'window' },
  'raw_sql': { label: 'Custom SQL', subtype: 'raw_sql' },
  'report': { label: 'Report', subtype: 'report' },
};

function getNodeTypeInfo(nodeType: string): { label: string; subtype: string } {
  const normalized = nodeType.toLowerCase();
  
  // Direct match
  if (NODE_TYPE_MAP[normalized]) {
    return NODE_TYPE_MAP[normalized];
  }
  
  // Check includes patterns
  for (const [key, value] of Object.entries(NODE_TYPE_MAP)) {
    if (normalized.includes(key) || key.includes(normalized)) {
      return value;
    }
  }
  
  // Default fallback
  return { label: nodeType, subtype: 'default' };
}

/**
 * Page Object for the Workflow Canvas
 * Handles node operations, drag-drop, workflow execution, and canvas interactions
 */
export class WorkflowCanvas {
  readonly page: Page;
  readonly canvas: Locator;
  readonly emptyState: Locator;
  readonly nodeContainer: Locator;
  readonly miniMap: Locator;
  readonly controls: Locator;
  readonly executeButton: Locator;
  readonly saveButton: Locator;
  readonly loadButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.canvas = page.locator('.react-flow').or(page.locator('[data-testid="workflow-canvas"]'));
    this.emptyState = page.locator('text=/your canvas is empty|Build Your Pipeline/i');
    this.nodeContainer = page.locator('.react-flow__node');
    this.miniMap = page.locator('.react-flow__minimap');
    this.controls = page.locator('.react-flow__controls');
    this.executeButton = page.locator('button:has-text("Execute"), button:has-text("Run")').or(page.locator('[data-testid="execute-workflow-btn"]'));
    this.saveButton = page.locator('button:has-text("Save")').or(page.locator('[data-testid="save-workflow-btn"]'));
    this.loadButton = page.locator('button:has-text("Load"), button:has-text("Open")').or(page.locator('[data-testid="load-workflow-btn"]'));
  }

  /**
   * Wait for the canvas to be visible and ready
   */
  async waitForReady() {
    await expect(this.canvas).toBeVisible({ timeout: 30000 });
  }

  /**
   * Check if canvas is empty (no nodes)
   */
  async isEmpty(): Promise<boolean> {
    const nodeCount = await this.nodeContainer.count();
    return nodeCount === 0;
  }

  /**
   * Get the count of nodes on the canvas
   */
  async getNodeCount(): Promise<number> {
    return await this.nodeContainer.count();
  }

  /**
   * Drag a node type from the sidebar and drop it on the canvas
   * @param nodeType - The type of node to drag (e.g., 'input', 'filter', 'output')
   * @param position - Optional position to drop the node {x, y}
   */
  async dragNodeToCanvas(nodeType: string, position?: { x: number; y: number }) {
    const { label } = getNodeTypeInfo(nodeType);

    const palettePanel = this.page.locator('[data-testid="palette"], .palette, aside').filter({
      has: this.page.getByText('CSV/Excel File'),
    }).first();
    
    const sidebarItem = palettePanel.getByText(label, { exact: false }).first();

    await expect(sidebarItem).toBeVisible({ timeout: 10000 });

    const canvasBox = await this.canvas.boundingBox();
    if (!canvasBox) throw new Error('Canvas not found');

    const dropX = position?.x ?? canvasBox.x + canvasBox.width / 2;
    const dropY = position?.y ?? canvasBox.y + canvasBox.height / 2;

    await sidebarItem.dragTo(this.canvas, {
      targetPosition: { x: dropX, y: dropY },
    });
  }

  /**
   * Get the technical subtype for a node label
   * @param label - The user-friendly label of the node type
   */
  getTechnicalSubtype(label: string): string {
    const { subtype } = getNodeTypeInfo(label);
    return subtype;
  }

  /**
   * Click on a node by its label or index
   * @param nodeLabel - The label of the node to click (string or RegExp)
   */
  async clickNode(nodeLabel: string | RegExp) {
    const node = this.nodeContainer.filter({ hasText: nodeLabel }).first();
    await expect(node).toBeVisible();
    await node.click({ force: true });
    // Verify it's selected (React Flow adds a 'selected' class)
    await expect(node).toHaveClass(/selected/);
  }

  /**
   * Select a node by index
   * @param index - The index of the node (0-based)
   */
  async selectNodeByIndex(index: number) {
    const node = this.nodeContainer.nth(index);
    await node.scrollIntoViewIfNeeded();
    await node.click({ force: true });
  }

  /**
   * Delete the currently selected node
   */
  async deleteSelectedNode() {
    await this.page.evaluate(() => {
      const el = document.activeElement as HTMLElement;
      if (el) el.blur();
    });
    await this.page.keyboard.press('Delete');
    await this.page.keyboard.press('Backspace');
  }

  /**
   * Connect two nodes by dragging from source to target
   * @param sourceLabel - The label of the source node
   * @param targetLabel - The label of the target node
   */
  async connectNodes(sourceLabel: string | RegExp, targetLabel: string | RegExp) {
    const sourceNode = this.nodeContainer.filter({ hasText: sourceLabel }).first();
    const targetNode = this.nodeContainer.filter({ hasText: targetLabel }).first();

    const sourceHandle = sourceNode.locator('.react-flow__handle-bottom, .react-flow__handle[data-handlepos="bottom"], .react-flow__handle.source');
    const targetHandle = targetNode.locator('.react-flow__handle-top, .react-flow__handle[data-handlepos="top"], .react-flow__handle.target');

    await sourceHandle.dragTo(targetHandle, { force: true });
  }

  /**
   * Execute the workflow
   */
  async execute() {
    await this.executeButton.click();
  }

  /**
   * Wait for workflow execution to complete
   */
  async waitForExecutionComplete() {
    await this.page.locator('[data-testid="execution-success"]')
      .or(this.page.locator('text=/executed successfully/i'))
      .waitFor({ state: 'visible', timeout: 60000 });
  }

  /**
   * Get the row count displayed on a node
   * @param nodeLabel - The label of the node
   */
  async getNodeRowCount(nodeLabel: string | RegExp): Promise<string> {
    const node = this.nodeContainer.filter({ hasText: nodeLabel }).first();
    const rowCount = node.locator('text=/rows/i');
    return await rowCount.textContent() || '';
  }

  /**
   * Check if a node exists on the canvas
   * @param nodeLabel - The label of the node to check
   */
  async hasNode(nodeLabel: string | RegExp): Promise<boolean> {
    const node = this.nodeContainer.filter({ hasText: nodeLabel });
    const count = await node.count();
    return count > 0;
  }

  /**
   * Get all node labels on the canvas
   */
  async getAllNodeLabels(): Promise<string[]> {
    const labels: string[] = [];
    const count = await this.nodeContainer.count();
    for (let i = 0; i < count; i++) {
      const node = this.nodeContainer.nth(i);
      const text = await node.textContent();
      if (text) labels.push(text);
    }
    return labels;
  }

  /**
   * Pan the canvas using the controls
   */
  async panCanvas(direction: 'up' | 'down' | 'left' | 'right') {
    const panButton = this.controls.locator(`button[aria-label*="${direction}" i], button[title*="${direction}" i]`);
    await panButton.click();
  }

  /**
   * Zoom the canvas
   */
  async zoomIn() {
    const zoomInButton = this.controls.locator('button[aria-label*="zoom in" i], button[title*="zoom in" i]');
    await zoomInButton.click();
  }

  async zoomOut() {
    const zoomOutButton = this.controls.locator('button[aria-label*="zoom out" i], button[title*="zoom out" i]');
    await zoomOutButton.click();
  }

  /**
   * Fit the view to show all nodes
   */
  async fitView() {
    const fitButton = this.controls.locator('button[aria-label*="fit" i], button[title*="fit" i]');
    if (await fitButton.isVisible()) {
      await fitButton.click();
    }
  }

  /**
   * Undo the last action
   */
  async undo() {
    const isMac = await this.page.evaluate(() => /Mac|iPod|iPhone|iPad|Macintosh/.test(navigator.userAgent));
    if (isMac) {
      await this.page.keyboard.press('Meta+Z');
    } else {
      await this.page.keyboard.press('Control+Z');
    }
  }

  /**
   * Redo the last undone action
   */
  async redo() {
    const isMac = await this.page.evaluate(() => /Mac|iPod|iPhone|iPad|Macintosh/.test(navigator.userAgent));
    if (isMac) {
      await this.page.keyboard.press('Meta+Shift+Z');
    } else {
      await this.page.keyboard.press('Control+Y');
    }
  }
}
