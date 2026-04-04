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
    this.emptyState = page.locator('text=/your canvas is empty/i');
    this.nodeContainer = page.locator('.react-flow__node');
    this.miniMap = page.locator('.react-flow__minimap');
    this.controls = page.locator('.react-flow__controls');
    this.executeButton = page.locator('button:has-text("Execute")').or(page.locator('[data-testid="execute-workflow-btn"]'));
    this.saveButton = page.locator('button:has-text("Save")').or(page.locator('[data-testid="save-workflow-btn"]'));
    this.loadButton = page.locator('button:has-text("Load")').or(page.locator('[data-testid="load-workflow-btn"]'));
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
    const sidebarItem = this.page.locator(
      `[data-testid="node-palette-item-${nodeType}"], [data-testid*="${nodeType}"], text=/${nodeType}/i`
    ).first();

    const canvasBox = await this.canvas.boundingBox();
    if (!canvasBox) throw new Error('Canvas not found');

    const dropX = position?.x ?? canvasBox.x + canvasBox.width / 2;
    const dropY = position?.y ?? canvasBox.y + canvasBox.height / 2;

    await sidebarItem.dragTo(this.canvas, {
      targetPosition: { x: dropX, y: dropY },
    });
  }

  /**
   * Click on a node by its label or index
   * @param nodeLabel - The label of the node to click
   */
  async clickNode(nodeLabel: string) {
    const node = this.nodeContainer.filter({ hasText: nodeLabel }).first();
    await expect(node).toBeVisible();
    await node.click();
  }

  /**
   * Select a node by index
   * @param index - The index of the node (0-based)
   */
  async selectNodeByIndex(index: number) {
    const nodes = this.nodeContainer.all();
    const node = (await nodes)[index];
    await node.click();
  }

  /**
   * Delete the currently selected node
   */
  async deleteSelectedNode() {
    await this.page.keyboard.press('Delete');
  }

  /**
   * Connect two nodes by dragging from source to target
   * @param sourceLabel - The label of the source node
   * @param targetLabel - The label of the target node
   */
  async connectNodes(sourceLabel: string, targetLabel: string) {
    const sourceNode = this.nodeContainer.filter({ hasText: sourceLabel }).first();
    const targetNode = this.nodeContainer.filter({ hasText: targetLabel }).first();

    const sourceHandle = sourceNode.locator('.react-flow__handle-bottom, .react-flow__handle[data-handlepos="bottom"]');
    const targetHandle = targetNode.locator('.react-flow__handle-top, .react-flow__handle[data-handlepos="top"]');

    await sourceHandle.dragTo(targetHandle);
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
    await expect(this.page.locator('[data-testid="execution-success"], text=/executed successfully/i')).toBeVisible({
      timeout: 60000,
    });
  }

  /**
   * Get the row count displayed on a node
   * @param nodeLabel - The label of the node
   */
  async getNodeRowCount(nodeLabel: string): Promise<string> {
    const node = this.nodeContainer.filter({ hasText: nodeLabel }).first();
    const rowCount = node.locator('text=/rows/i');
    return await rowCount.textContent() || '';
  }

  /**
   * Check if a node exists on the canvas
   * @param nodeLabel - The label of the node to check
   */
  async hasNode(nodeLabel: string): Promise<boolean> {
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
    const panButton = this.controls.locator(`button[aria-label*="${direction}"], button[title*="${direction}"]`);
    await panButton.click();
  }

  /**
   * Zoom the canvas
   */
  async zoomIn() {
    const zoomInButton = this.controls.locator('button[aria-label*="zoom in"], button[title*="zoom in"]');
    await zoomInButton.click();
  }

  async zoomOut() {
    const zoomOutButton = this.controls.locator('button[aria-label*="zoom out"], button[title*="zoom out"]');
    await zoomOutButton.click();
  }

  /**
   * Fit the view to show all nodes
   */
  async fitView() {
    const fitButton = this.controls.locator('button[aria-label*="fit"], button[title*="fit"]');
    await fitButton.click();
  }

  /**
   * Undo the last action
   */
  async undo() {
    const isMac = await this.page.evaluate(() => /Mac|iPod|iPhone|iPad/.test(navigator.userAgent));
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
    const isMac = await this.page.evaluate(() => /Mac|iPod|iPhone|iPad/.test(navigator.userAgent));
    if (isMac) {
      await this.page.keyboard.press('Meta+Shift+Z');
    } else {
      await this.page.keyboard.press('Control+Y');
    }
  }
}
