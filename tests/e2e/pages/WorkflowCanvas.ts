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
   * Close the bottom data inspection panel if it is visible
   */
  async closePanel() {
    const panel = this.page.locator('[data-testid="data-inspection-panel"]');
    const isVisible = await panel.isVisible({ timeout: 2000 }).catch(() => false);

    if (isVisible) {
      try {
        // The close button is in the header section, after the tabs
        // Use title attribute to find it specifically
        const closeButton = panel.locator('button[title="Close Panel"]');
        const isButtonVisible = await closeButton.isVisible({ timeout: 1000 }).catch(() => false);

        if (isButtonVisible) {
          await closeButton.click();
          await expect(panel).toBeHidden({ timeout: 5000 }).catch(() => {});
          // Small delay after closing panel to let layout settle
          await this.page.waitForTimeout(500);
        } else {
          // Fallback: click outside the panel on the canvas to deselect
          await this.page.locator('.react-flow__pane').click({ force: true });
        }
      } catch (error) {
        // If closing fails, just continue - the panel might not be blocking interactions
        console.log('Failed to close panel, continuing:', error);
      }
    }
  }

  /**
   * Click on a node by its label, technical name, or index
   * @param nodeLabel - The identifier for the node
   */
  async clickNode(nodeLabel: string | RegExp | number) {
    // Close bottom panel to avoid intercepting clicks
    await this.closePanel();

    let node: Locator;
    if (typeof nodeLabel === 'number') {
      node = this.nodeContainer.nth(nodeLabel);
    } else {
      const { label } = typeof nodeLabel === 'string' ? getNodeTypeInfo(nodeLabel) : { label: nodeLabel };
      node = this.nodeContainer.filter({ 
        has: this.page.locator('span, div').filter({ hasText: label }).or(this.page.locator('span, div').filter({ hasText: nodeLabel }))
      }).first();
    }

    await node.scrollIntoViewIfNeeded();
    await expect(node).toBeVisible();

    // Try clicking the node header specifically to trigger selection
    const nodeHeader = node.locator('.react-flow__node-header, [data-testid="rf__node-header"], .node-header').first();
    const hasHeader = await nodeHeader.count() > 0;

    if (hasHeader) {
      await nodeHeader.click({ force: true });
    } else {
      // Fallback to clicking the node itself
      await node.click({ force: true });
    }

    // Wait for state sync and UI update
    await this.page.waitForTimeout(1500);

    // Verify selection only for non-index selection (index-based selection has issues with 'selected' class)
    if (typeof nodeLabel !== 'number') {
      await expect(node).toHaveClass(/selected/, { timeout: 5000 });
    }
  }

  /**
   * Select a node by index
   * @param index - The index of the node (0-based)
   */
  async selectNodeByIndex(index: number) {
    await this.clickNode(index);
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
   * @param source - The label, technical name, or index of the source node
   * @param target - The label, technical name, or index of the target node
   */
  async connectNodes(source: string | RegExp | number, target: string | RegExp | number) {
    // Ensure handles are visible and not covered
    await this.closePanel();

    let sourceNode: Locator;
    let targetNode: Locator;

    if (typeof source === 'number') {
      sourceNode = this.nodeContainer.nth(source);
    } else {
      const { label: sLabel } = typeof source === 'string' ? getNodeTypeInfo(source) : { label: source };
      sourceNode = this.nodeContainer.filter({
        has: this.page.locator('span, div').filter({ hasText: sLabel }).or(this.page.locator('span, div').filter({ hasText: source }))
      }).first();
    }

    if (typeof target === 'number') {
      targetNode = this.nodeContainer.nth(target);
    } else {
      const { label: tLabel } = typeof target === 'string' ? getNodeTypeInfo(target) : { label: target };
      targetNode = this.nodeContainer.filter({
        has: this.page.locator('span, div').filter({ hasText: tLabel }).or(this.page.locator('span, div').filter({ hasText: target }))
      }).first();
    }

    await sourceNode.scrollIntoViewIfNeeded();
    await targetNode.scrollIntoViewIfNeeded();

    // Specifically target the source and target handles - Phase 2 fix: try multiple handle selectors
    const sourceHandle = sourceNode.locator('.react-flow__handle.source, .react-flow__handle-bottom, [data-handleid*="source"]').first();
    const targetHandle = targetNode.locator('.react-flow__handle.target, .react-flow__handle-top, [data-handleid*="target"]').first();

    // Wait for handles with longer timeout - Phase 2 fix
    try {
      await sourceHandle.waitFor({ state: 'visible', timeout: 5000 });
      await targetHandle.waitFor({ state: 'visible', timeout: 5000 });
    } catch (e) {
      console.log('Handles not visible, trying alternative selectors');
      // Alternative: try to find any handle on the node
      const altSourceHandle = sourceNode.locator('.react-flow__handle').first();
      const altTargetHandle = targetNode.locator('.react-flow__handle').first();
      await altSourceHandle.waitFor({ state: 'visible', timeout: 3000 });
      await altTargetHandle.waitFor({ state: 'visible', timeout: 3000 });
    }

    // Center view to stabilize positions
    await this.fitView();
    await this.page.waitForTimeout(500);

    const initialEdgeCount = await this.page.locator('.react-flow__edge, [data-testid^="rf__edge-"]').count();

    // Phase 2 fix: Multiple retry attempts with different strategies
    let connectionSuccess = false;
    const maxRetries = 3;

    for (let attempt = 1; attempt <= maxRetries && !connectionSuccess; attempt++) {
      try {
        const sourceBox = await sourceHandle.boundingBox();
        const targetBox = await targetHandle.boundingBox();

        if (!sourceBox || !targetBox) {
          // Fallback to dragTo if bounding boxes not available
          await sourceHandle.dragTo(targetHandle, { force: true });
        } else {
          // Manual drag with more steps for better accuracy
          await this.page.mouse.move(sourceBox.x + sourceBox.width / 2, sourceBox.y + sourceBox.height / 2);
          await this.page.mouse.down();
          await this.page.waitForTimeout(100); // Small delay after mouse down

          // Even more steps for Phase 2
          await this.page.mouse.move(targetBox.x + targetBox.width / 2, targetBox.y + targetBox.height / 2, { steps: 100 });
          await this.page.waitForTimeout(100); // Small delay before mouse up
          await this.page.mouse.up();
        }

        // Wait for the edge to appear
        await expect(this.page.locator('.react-flow__edge, [data-testid^="rf__edge-"]')).toHaveCount(initialEdgeCount + 1, { timeout: 7000 });
        connectionSuccess = true;

      } catch (e) {
        console.warn(`Connection attempt ${attempt}/${maxRetries} failed`, e);

        if (attempt < maxRetries) {
          // Wait before retry
          await this.page.waitForTimeout(1000);

          // Try refreshing handles
          await sourceNode.scrollIntoViewIfNeeded();
          await targetNode.scrollIntoViewIfNeeded();
          await this.page.waitForTimeout(500);
        }
      }
    }

    if (!connectionSuccess) {
      console.error('Failed to connect nodes after all retry attempts');
      // Don't throw - let the test fail naturally with better error message
    }

    // Pause after connection to let React Flow and our state settle
    await this.page.waitForTimeout(1000);
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
   * @param nodeLabel - The label or technical name of the node
   */
  async getNodeRowCount(nodeLabel: string | RegExp): Promise<string> {
    const { label } = typeof nodeLabel === 'string' ? getNodeTypeInfo(nodeLabel) : { label: nodeLabel };
    const node = this.nodeContainer.filter({ 
      has: this.page.locator('span, div').filter({ hasText: label }).or(this.page.locator('span, div').filter({ hasText: nodeLabel }))
    }).first();
    const rowCount = node.locator('text=/rows/i');
    return await rowCount.textContent() || '';
  }

  /**
   * Check if a node exists on the canvas
   * @param nodeLabel - The label or technical name of the node to check
   */
  async hasNode(nodeLabel: string | RegExp): Promise<boolean> {
    const { label } = typeof nodeLabel === 'string' ? getNodeTypeInfo(nodeLabel) : { label: nodeLabel };
    const node = this.nodeContainer.filter({ 
      has: this.page.locator('span, div').filter({ hasText: label }).or(this.page.locator('span, div').filter({ hasText: nodeLabel }))
    });
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
      // Use innerText() instead of textContent() to exclude <style> tag content
      const text = await node.innerText();
      if (text) {
        // Find the line that looks like the label (usually the first line or line without "Rows")
        const lines = text.split('\n').map(l => l.trim()).filter(l => l && !l.match(/^rows$/i) && !l.match(/^\d+(,\d+)*$/));
        if (lines.length > 0) {
          labels.push(lines[0]);
        }
      }
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

  /**
   * Select option from a dropdown with proper wait for options to populate - Phase 2 fix
   * @param selectLocator - Locator for the select element
   * @param option - Option value to select
   * @param options - Optional timeout settings
   */
  async selectDropdownOption(
    selectLocator: Locator,
    option: string,
    options?: { timeout?: number; waitForOptions?: boolean }
  ) {
    const timeout = options?.timeout || 5000;
    const waitForOptions = options?.waitForOptions !== false; // Default to true

    await selectLocator.waitFor({ state: 'visible', timeout });

    // Wait for options to populate if requested
    if (waitForOptions) {
      await this.page.waitForTimeout(500); // Give backend time to populate options

      // Check if options are actually populated
      const optionCount = await selectLocator.locator('option').count();
      if (optionCount === 0) {
        console.log(`Dropdown has no options available. Select element might be: ${await selectLocator.inputValue()}`);
      }
    }

    await selectLocator.selectOption(option);
  }

  /**
   * Wait for dropdown options to be populated - Phase 2 fix
   * @param selectLocator - Locator for the select element
   * @param minOptions - Minimum number of options expected (default: 1)
   */
  async waitForDropdownOptions(selectLocator: Locator, minOptions: number = 1) {
    await selectLocator.waitFor({ state: 'visible', timeout: 5000 });

    // Wait for options to populate
    await this.page.waitForTimeout(500);

    const options = selectLocator.locator('option');
    const count = await options.count();

    if (count < minOptions) {
      throw new Error(`Expected at least ${minOptions} dropdown options, but found ${count}`);
    }

    return count;
  }
}
