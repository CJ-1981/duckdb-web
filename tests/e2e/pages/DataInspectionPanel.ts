import { Page, Locator, expect } from '@playwright/test';

/**
 * Page Object for the Data Inspection Panel
 * Handles data preview, schema view, and statistics verification
 */
export class DataInspectionPanel {
  readonly page: Page;
  readonly panel: Locator;
  readonly tabs: {
    data: Locator;
    schema: Locator;
    stats: Locator;
  };
  readonly dataTable: Locator;
  readonly schemaTable: Locator;
  readonly statsContainer: Locator;

  constructor(page: Page) {
    this.page = page;
    this.panel = page.locator('[data-testid="data-inspection-panel"], .data-inspection-panel').or(
      page.locator('text=/select a node to inspect/i').locator('..')
    );
    this.tabs = {
      data: page.locator('button:has-text("Data Table"), button:has-text("data")'),
      schema: page.locator('button:has-text("Schema"), button:has-text("schema")'),
      stats: page.locator('button:has-text("Statistics"), button:has-text("stats")'),
    };
    this.dataTable = page.locator('table:has(th)').first();
    this.schemaTable = page.locator('table:has(th)').nth(1);
    this.statsContainer = page.locator('[data-testid="column-stats"], .column-stats');
  }

  /**
   * Wait for the panel to be visible
   */
  async waitForVisible() {
    await expect(this.panel).toBeVisible({ timeout: 10000 });
  }

  /**
   * Switch to the Data tab
   */
  async switchToDataTab() {
    await this.tabs.data.click();
    await expect(this.dataTable).toBeVisible();
  }

  /**
   * Switch to the Schema tab
   */
  async switchToSchemaTab() {
    await this.tabs.schema.click();
    await expect(this.schemaTable).toBeVisible();
  }

  /**
   * Switch to the Statistics tab
   */
  async switchToStatsTab() {
    await this.tabs.stats.click();
    await expect(this.statsContainer).toBeVisible();
  }

  /**
   * Get the column headers from the data table
   */
  async getDataColumns(): Promise<string[]> {
    await this.switchToDataTab();
    const headers = await this.dataTable.locator('th').allTextContents();
    return headers.map(h => h.trim());
  }

  /**
   * Get the row count from the data preview
   */
  async getDataRowCount(): Promise<number> {
    await this.switchToDataTab();
    const rows = await this.dataTable.locator('tbody tr').count();
    return rows;
  }

  /**
   * Get all data from the data table
   */
  async getTableData(): Promise<string[][]> {
    await this.switchToDataTab();
    const rows = await this.dataTable.locator('tbody tr').all();
    const data: string[][] = [];

    for (const row of rows) {
      const cells = await row.locator('td').allTextContents();
      data.push(cells.map(c => c.trim()));
    }

    return data;
  }

  /**
   * Get the value of a specific cell
   * @param rowIndex - The row index (0-based)
   * @param columnName - The column name
   */
  async getCellValue(rowIndex: number, columnName: string): Promise<string> {
    const columns = await this.getDataColumns();
    const colIndex = columns.indexOf(columnName);
    if (colIndex === -1) throw new Error(`Column "${columnName}" not found`);

    const cell = this.dataTable.locator('tbody tr').nth(rowIndex).locator('td').nth(colIndex);
    return (await cell.textContent())?.trim() || '';
  }

  /**
   * Get schema information for all columns
   */
  async getSchema(): Promise<Array<{ name: string; type: string; category: string }>> {
    await this.switchToSchemaTab();
    const rows = await this.schemaTable.locator('tbody tr').all();
    const schema: Array<{ name: string; type: string; category: string }> = [];

    for (const row of rows) {
      const cells = await row.locator('td').allTextContents();
      schema.push({
        name: cells[0]?.trim() || '',
        type: cells[1]?.trim() || '',
        category: cells[2]?.trim() || '',
      });
    }

    return schema;
  }

  /**
   * Get the type of a specific column
   * @param columnName - The column name
   */
  async getColumnType(columnName: string): Promise<string> {
    const schema = await this.getSchema();
    const column = schema.find(col => col.name === columnName);
    return column?.type || '';
  }

  /**
   * Get statistics for a specific column
   * @param columnName - The column name
   */
  async getColumnStats(columnName: string): Promise<{
    count: string;
    distinct: string;
    nulls: string;
    nullPct: string;
  } | null> {
    await this.switchToStatsTab();
    const statBlock = this.statsContainer.filter({ hasText: columnName });

    const isVisible = await statBlock.isVisible().catch(() => false);
    if (!isVisible) return null;

    const getText = async (label: string) => {
      const element = statBlock.locator(`text=${label}`).locator('..').locator('div').first();
      return (await element.textContent())?.trim() || '';
    };

    return {
      count: await getText('Non-Null'),
      distinct: await getText('Distinct'),
      nulls: await getText('Nulls'),
      nullPct: await getText('Null %'),
    };
  }

  /**
   * Verify that the data preview contains specific values
   * @param expectedData - Array of expected rows
   */
  async verifyDataContains(expectedData: string[][]): Promise<boolean> {
    const actualData = await this.getTableData();

    for (const expectedRow of expectedData) {
      const match = actualData.some(actualRow =>
        expectedRow.every((cell, i) => actualRow[i] === cell)
      );
      if (!match) return false;
    }

    return true;
  }

  /**
   * Check if the panel shows "no data" message
   */
  async isNoDataMessage(): Promise<boolean> {
    const noDataMessage = this.panel.locator('text=/no sample data|execute the workflow/i');
    return await noDataMessage.isVisible().catch(() => false);
  }

  /**
   * Copy schema in a specific format
   * @param format - The format to copy ('md', 'json', or 'sql')
   */
  async copySchema(format: 'md' | 'json' | 'sql') {
    const button = this.panel.locator(`button:has-text("${format.toUpperCase()}"), button:has-text("${format}")`);
    await button.click();
  }

  /**
   * Trigger full dataset statistics computation
   */
  async computeFullStats() {
    const button = this.panel.locator('button:has-text("Full Dataset Analysis")');
    await button.click();
  }

  /**
   * Wait for full stats computation to complete
   */
  async waitForFullStats() {
    await expect(this.panel.locator('text=/full dataset/i')).toBeVisible({ timeout: 60000 });
  }

  /**
   * Get the sample row count displayed in the panel
   */
  async getSampleRowCount(): Promise<string> {
    const text = await this.panel.locator('text=/showing.*sample rows/i').textContent();
    const match = text?.match(/showing (\d+) sample rows/i);
    return match?.[1] || '0';
  }
}
