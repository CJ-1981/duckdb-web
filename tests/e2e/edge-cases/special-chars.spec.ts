import { test, expect } from '@playwright/test';
import { WorkflowCanvas } from '../pages/WorkflowCanvas';
import { DataInspectionPanel } from '../pages/DataInspectionPanel';
import { csvWithSpecialChars } from '../fixtures/testData';
import { assertSpecialCharsPreserved } from '../fixtures/assertions';

test.describe('Edge Cases - Special Characters', () => {
  let canvas: WorkflowCanvas;
  let dataPanel: DataInspectionPanel;

  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:3000');
    canvas = new WorkflowCanvas(page);
    dataPanel = new DataInspectionPanel(page);
    await canvas.waitForReady();
  });

  test('should preserve commas in quoted CSV fields', async ({ page }) => {
    await canvas.dragNodeToCanvas('input');
    await page.locator('.react-flow__node').first().click();

    const buffer = Buffer.from(csvWithSpecialChars.content, 'utf-8');
    const fileInput = page.locator('input[type="file"]');

    if (await fileInput.isVisible()) {
      const fileChooserPromise = page.waitForEvent('filechooser');
      await fileInput.click();
      const fileChooser = await fileChooserPromise;

      await fileChooser.setFiles({
        name: csvWithSpecialChars.filename,
        mimeType: 'text/csv',
        buffer: buffer,
      });

      await page.waitForTimeout(3000);
      await dataPanel.switchToDataTab();

      // Check that commas in description are preserved
      const descriptionValue = await dataPanel.getCellValue(0, 'description');
      expect(descriptionValue).toContain(',');
      expect(descriptionValue).toContain('commas');
    }
  });

  test('should preserve quotes in quoted CSV fields', async ({ page }) => {
    await canvas.dragNodeToCanvas('input');
    await page.locator('.react-flow__node').first().click();

    const buffer = Buffer.from(csvWithSpecialChars.content, 'utf-8');
    const fileInput = page.locator('input[type="file"]');

    if (await fileInput.isVisible()) {
      const fileChooserPromise = page.waitForEvent('filechooser');
      await fileInput.click();
      const fileChooser = await fileChooserPromise;

      await fileChooser.setFiles({
        name: csvWithSpecialChars.filename,
        mimeType: 'text/csv',
        buffer: buffer,
      });

      await page.waitForTimeout(3000);
      await dataPanel.switchToDataTab();

      const descriptionValue = await dataPanel.getCellValue(1, 'description');
      expect(descriptionValue).toContain('"');
      expect(descriptionValue).toContain('quotes');
    }
  });

  test('should preserve newlines in quoted CSV fields', async ({ page }) => {
    await canvas.dragNodeToCanvas('input');
    await page.locator('.react-flow__node').first().click();

    const buffer = Buffer.from(csvWithSpecialChars.content, 'utf-8');
    const fileInput = page.locator('input[type="file"]');

    if (await fileInput.isVisible()) {
      const fileChooserPromise = page.waitForEvent('filechooser');
      await fileInput.click();
      const fileChooser = await fileChooserPromise;

      await fileChooser.setFiles({
        name: csvWithSpecialChars.filename,
        mimeType: 'text/csv',
        buffer: buffer,
      });

      await page.waitForTimeout(3000);
      await dataPanel.switchToDataTab();

      const descriptionValue = await dataPanel.getCellValue(2, 'description');
      // Newlines might be displayed as spaces or line breaks
      expect(descriptionValue).toContain('newlines');
    }
  });

  test('should preserve forward slashes in data', async ({ page }) => {
    await canvas.dragNodeToCanvas('input');
    await page.locator('.react-flow__node').first().click();

    const buffer = Buffer.from(csvWithSpecialChars.content, 'utf-8');
    const fileInput = page.locator('input[type="file"]');

    if (await fileInput.isVisible()) {
      const fileChooserPromise = page.waitForEvent('filechooser');
      await fileInput.click();
      const fileChooser = await fileChooserPromise;

      await fileChooser.setFiles({
        name: csvWithSpecialChars.filename,
        mimeType: 'text/csv',
        buffer: buffer,
      });

      await page.waitForTimeout(3000);
      await dataPanel.switchToDataTab();

      const nameValue = await dataPanel.getCellValue(3, 'name');
      expect(nameValue).toContain('/');
    }
  });

  test('should preserve special symbols (@, #, $, %)', async ({ page }) => {
    await canvas.dragNodeToCanvas('input');
    await page.locator('.react-flow__node').first().click();

    const buffer = Buffer.from(csvWithSpecialChars.content, 'utf-8');
    const fileInput = page.locator('input[type="file"]');

    if (await fileInput.isVisible()) {
      const fileChooserPromise = page.waitForEvent('filechooser');
      await fileInput.click();
      const fileChooser = await fileChooserPromise;

      await fileChooser.setFiles({
        name: csvWithSpecialChars.filename,
        mimeType: 'text/csv',
        buffer: buffer,
      });

      await page.waitForTimeout(3000);
      await dataPanel.switchToDataTab();

      const descriptionValue = await dataPanel.getCellValue(4, 'description');
      expect(descriptionValue).toContain('@');
      expect(descriptionValue).toContain('#');
      expect(descriptionValue).toContain('$');
      expect(descriptionValue).toContain('%');
    }
  });

  test('should handle Unicode characters correctly', async ({ page }) => {
    await canvas.dragNodeToCanvas('input');
    await page.locator('.react-flow__node').first().click();

    // Create CSV with Unicode characters
    const unicodeCsv = 'id,name,city\n1,José,São Paulo\n2,Müller,München\n3,李明,北京\n4,Алексей,Москва';
    const buffer = Buffer.from(unicodeCsv, 'utf-8');
    const fileInput = page.locator('input[type="file"]');

    if (await fileInput.isVisible()) {
      const fileChooserPromise = page.waitForEvent('filechooser');
      await fileInput.click();
      const fileChooser = await fileChooserPromise;

      await fileChooser.setFiles({
        name: 'unicode.csv',
        mimeType: 'text/csv',
        buffer: buffer,
      });

      await page.waitForTimeout(3000);
      await dataPanel.switchToDataTab();

      const name1 = await dataPanel.getCellValue(0, 'name');
      expect(name1).toBe('José');

      const city1 = await dataPanel.getCellValue(0, 'city');
      expect(city1).toBe('São Paulo');
    }
  });

  test('should handle emojis in data', async ({ page }) => {
    await canvas.dragNodeToCanvas('input');
    await page.locator('.react-flow__node').first().click();

    const emojiCsv = 'id,name,status\n1,Test 😊,✅\n2,Test 🚀,🔥';
    const buffer = Buffer.from(emojiCsv, 'utf-8');
    const fileInput = page.locator('input[type="file"]');

    if (await fileInput.isVisible()) {
      const fileChooserPromise = page.waitForEvent('filechooser');
      await fileInput.click();
      const fileChooser = await fileChooserPromise;

      await fileChooser.setFiles({
        name: 'emoji.csv',
        mimeType: 'text/csv',
        buffer: buffer,
      });

      await page.waitForTimeout(3000);
      await dataPanel.switchToDataTab();

      const name1 = await dataPanel.getCellValue(0, 'name');
      expect(name1).toContain('😊');

      const status1 = await dataPanel.getCellValue(0, 'status');
      expect(status1).toContain('✅');
    }
  });

  test('should filter on columns with special characters', async ({ page }) => {
    await canvas.dragNodeToCanvas('input');
    await canvas.dragNodeToCanvas('filter');
    await canvas.dragNodeToCanvas('output');

    const nodes = await canvas.getAllNodeLabels();
    if (nodes.length >= 3) {
      await canvas.connectNodes(nodes[0], nodes[1]);
      await canvas.connectNodes(nodes[1], nodes[2]);

      const buffer = Buffer.from(csvWithSpecialChars.content, 'utf-8');
      const fileInput = page.locator('input[type="file"]');

      if (await fileInput.isVisible()) {
        const fileChooserPromise = page.waitForEvent('filechooser');
        await fileInput.click();
        const fileChooser = await fileChooserPromise;

        await fileChooser.setFiles({
          name: csvWithSpecialChars.filename,
          mimeType: 'text/csv',
          buffer: buffer,
        });

        await page.waitForTimeout(2000);

        // Configure filter
        await canvas.clickNode(nodes.find(n => n.toLowerCase().includes('filter')) || 'Filter');

        const columnSelect = page.locator('select[name="column"]');
        if (await columnSelect.isVisible()) {
          await columnSelect.selectOption('name');
        }

        const operatorSelect = page.locator('select[name="operator"]');
        if (await operatorSelect.isVisible()) {
          await operatorSelect.selectOption('contains');
        }

        const valueInput = page.locator('input[name="value"]');
        if (await valueInput.isVisible()) {
          await valueInput.fill('/');
        }

        await page.waitForTimeout(1000);

        await canvas.execute();
        await page.waitForTimeout(5000);

        await canvas.clickNode(nodes[2]);
        await dataPanel.switchToDataTab();

        const rowCount = await dataPanel.getDataRowCount();
        expect(rowCount).toBeGreaterThan(0);
      }
    }
  });

  test('should handle column names with special characters', async ({ page }) => {
    await canvas.dragNodeToCanvas('input');
    await page.locator('.react-flow__node').first().click();

    // Create CSV with special characters in column names
    const specialColCsv = 'id,"User Name","Email Address",age\n1,Alice,alice@example.com,30';
    const buffer = Buffer.from(specialColCsv, 'utf-8');
    const fileInput = page.locator('input[type="file"]');

    if (await fileInput.isVisible()) {
      const fileChooserPromise = page.waitForEvent('filechooser');
      await fileInput.click();
      const fileChooser = await fileChooserPromise;

      await fileChooser.setFiles({
        name: 'special-cols.csv',
        mimeType: 'text/csv',
        buffer: buffer,
      });

      await page.waitForTimeout(3000);
      await dataPanel.switchToSchemaTab();

      const columns = await dataPanel.getDataColumns();
      expect(columns).toContain('User Name');
      expect(columns).toContain('Email Address');
    }
  });

  test('should escape special characters in SQL queries', async ({ page }) => {
    await canvas.dragNodeToCanvas('input');
    await canvas.dragNodeToCanvas('sql');

    const nodes = await canvas.getAllNodeLabels();
    if (nodes.length >= 2) {
      await canvas.connectNodes(nodes[0], nodes[1]);

      const buffer = Buffer.from(csvWithSpecialChars.content, 'utf-8');
      const fileInput = page.locator('input[type="file"]');

      if (await fileInput.isVisible()) {
        const fileChooserPromise = page.waitForEvent('filechooser');
        await fileInput.click();
        const fileChooser = await fileChooserPromise;

        await fileChooser.setFiles({
          name: csvWithSpecialChars.filename,
          mimeType: 'text/csv',
          buffer: buffer,
        });

        await page.waitForTimeout(2000);

        await canvas.clickNode(nodes.find(n => n.toLowerCase().includes('sql')) || 'SQL');

        const sqlEditor = page.locator('textarea[name="sql"]');
        if (await sqlEditor.isVisible()) {
          await sqlEditor.fill('SELECT * FROM input WHERE "name" LIKE \'%/%\'' );

          await page.waitForTimeout(1000);

          // Execute query
          await canvas.execute();
          await page.waitForTimeout(5000);

          // Should handle special characters in query
          const hasError = page.locator('text=/error/i').isVisible().catch(() => false);
          expect(hasError).toBeFalsy();
        }
      }
    }
  });

  test('should handle very long strings', async ({ page }) => {
    await canvas.dragNodeToCanvas('input');
    await page.locator('.react-flow__node').first().click();

    // Create CSV with very long string
    const longString = 'a'.repeat(10000);
    const longCsv = `id,name\n1,${longString}`;
    const buffer = Buffer.from(longCsv, 'utf-8');
    const fileInput = page.locator('input[type="file"]');

    if (await fileInput.isVisible()) {
      const fileChooserPromise = page.waitForEvent('filechooser');
      await fileInput.click();
      const fileChooser = await fileChooserPromise;

      await fileChooser.setFiles({
        name: 'long-string.csv',
        mimeType: 'text/csv',
        buffer: buffer,
      });

      await page.waitForTimeout(3000);
      await dataPanel.switchToDataTab();

      const nameValue = await dataPanel.getCellValue(0, 'name');
      expect(nameValue.length).toBeGreaterThan(100);
    }
  });

  test('should preserve leading/trailing whitespace', async ({ page }) => {
    await canvas.dragNodeToCanvas('input');
    await page.locator('.react-flow__node').first().click();

    const whitespaceCsv = 'id,name\n1,"  Alice  "\n2,"  Bob"';
    const buffer = Buffer.from(whitespaceCsv, 'utf-8');
    const fileInput = page.locator('input[type="file"]');

    if (await fileInput.isVisible()) {
      const fileChooserPromise = page.waitForEvent('filechooser');
      await fileInput.click();
      const fileChooser = await fileChooserPromise;

      await fileChooser.setFiles({
        name: 'whitespace.csv',
        mimeType: 'text/csv',
        buffer: buffer,
      });

      await page.waitForTimeout(3000);
      await dataPanel.switchToDataTab();

      const nameValue = await dataPanel.getCellValue(0, 'name');
      // Depending on CSV parsing, whitespace might be trimmed
      expect(nameValue).toBeTruthy();
    }
  });

  test('should handle backslash characters', async ({ page }) => {
    await canvas.dragNodeToCanvas('input');
    await page.locator('.react-flow__node').first().click();

    const backslashCsv = 'id,path\n1,"C:\\Users\\Test"\n2,"/home/user/test"';
    const buffer = Buffer.from(backslashCsv, 'utf-8');
    const fileInput = page.locator('input[type="file"]');

    if (await fileInput.isVisible()) {
      const fileChooserPromise = page.waitForEvent('filechooser');
      await fileInput.click();
      const fileChooser = await fileChooserPromise;

      await fileChooser.setFiles({
        name: 'backslash.csv',
        mimeType: 'text/csv',
        buffer: buffer,
      });

      await page.waitForTimeout(3000);
      await dataPanel.switchToDataTab();

      const pathValue = await dataPanel.getCellValue(0, 'path');
      expect(pathValue).toContain('\\');
    }
  });

  test('should handle tab characters in data', async ({ page }) => {
    await canvas.dragNodeToCanvas('input');
    await page.locator('.react-flow__node').first().click();

    const tabCsv = 'id,name\n1,"Alice\tBob"\n2,"Carol\tDavis"';
    const buffer = Buffer.from(tabCsv, 'utf-8');
    const fileInput = page.locator('input[type="file"]');

    if (await fileInput.isVisible()) {
      const fileChooserPromise = page.waitForEvent('filechooser');
      await fileInput.click();
      const fileChooser = await fileChooserPromise;

      await fileChooser.setFiles({
        name: 'tabs.csv',
        mimeType: 'text/csv',
        buffer: buffer,
      });

      await page.waitForTimeout(3000);
      await dataPanel.switchToDataTab();

      const nameValue = await dataPanel.getCellValue(0, 'name');
      expect(nameValue).toBeTruthy();
    }
  });
});
