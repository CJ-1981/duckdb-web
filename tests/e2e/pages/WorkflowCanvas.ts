import { Page, Locator, expect } from '@playwright/test';

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
    // Map generic types to actual sidebar labels if needed
    let label = nodeType;
    const l = nodeType.toLowerCase();
    if (l === 'input' || l.includes('csv')) label = 'CSV/Excel File';
    else if (l === 'filter') label = 'Filter Records';
    else if (l === 'output' || l.includes('export')) label = 'Export File';
    else if (l === 'aggregate') label = 'Aggregate Data';
    else if (l === 'combine' || l === 'join') label = 'Combine Datasets';

    const sidebarItem = this.page.locator('aside').getByText(label, { exact: false }).first();

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
    const l = label.toLowerCase();
    if (l.includes('csv') || l.includes('excel') || l === 'input') return 'csv';
    if (l.includes('filter')) return 'filter';
    if (l.includes('combine') || l.includes('join')) return 'combine';
    if (l.includes('clean')) return 'clean';
    if (l.includes('aggregate')) return 'aggregate';
    if (l.includes('sort')) return 'sort';
    if (l.includes('limit')) return 'limit';
    if (l.includes('select')) return 'select';
    if (l.includes('add column') || l.includes('computed')) return 'computed';
    if (l.includes('rename')) return 'rename';
    if (l.includes('duplicate') || l.includes('distinct')) return 'distinct';
    if (l.includes('logic') || l.includes('case')) return 'case_when';
    if (l.includes('window')) return 'window';
    if (l.includes('sql')) return 'raw_sql';
    if (l.includes('report')) return 'report';
    if (l.includes('export')) return 'export';
    return 'default';
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
    // Ensure the page has focus for keyboard events
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
