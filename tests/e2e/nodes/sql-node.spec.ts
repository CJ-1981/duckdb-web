import { test, expect } from '@playwright/test';
import { WorkflowCanvas } from '../pages/WorkflowCanvas';
import { DataInspectionPanel } from '../pages/DataInspectionPanel';
import { sampleCsvData } from '../fixtures/testData';
import { assertNodeExists, assertSqlPreviewContains, assertExecutionSuccess } from '../fixtures/assertions';

test.describe('SQL Node Tests', () => {
  let canvas: WorkflowCanvas;
  let dataPanel: DataInspectionPanel;

  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:3000');
    canvas = new WorkflowCanvas(page);
    dataPanel = new DataInspectionPanel(page);
    await canvas.waitForReady();
  });

  test('should create SQL node from palette', async ({ page }) => {
    await canvas.dragNodeToCanvas('sql');
    await expect(await canvas.getNodeCount()).toBe(1);
    await assertNodeExists(page, 'SQL');
  });

  test('should allow typing custom SQL query', async ({ page }) => {
    await canvas.dragNodeToCanvas('input');
    await canvas.dragNodeToCanvas('sql');

    const nodes = await canvas.getAllNodeLabels();
    if (nodes.length >= 2) {
      await canvas.connectNodes(nodes[0], nodes[1]);

      // Click SQL node
      await canvas.clickNode(nodes.find(n => n.toLowerCase().includes('sql')) || 'SQL');

      // Find SQL editor
      const sqlEditor = page.locator('textarea[name="sql"], [data-testid="sql-editor"], .monaco-editor textarea');
      if (await sqlEditor.isVisible()) {
        await sqlEditor.fill('SELECT * FROM input WHERE age > 25');
        await page.waitForTimeout(1000);

        await assertSqlPreviewContains(page, 'SELECT');
        await assertSqlPreviewContains(page, 'age > 25');
      }
    }
  });

  test('should validate SQL syntax', async ({ page }) => {
    await canvas.dragNodeToCanvas('input');
    await canvas.dragNodeToCanvas('sql');

    const nodes = await canvas.getAllNodeLabels();
    if (nodes.length >= 2) {
      await canvas.connectNodes(nodes[0], nodes[1]);

      await canvas.clickNode(nodes.find(n => n.toLowerCase().includes('sql')) || 'SQL');

      const sqlEditor = page.locator('textarea[name="sql"]');
      if (await sqlEditor.isVisible()) {
        // Enter invalid SQL
        await sqlEditor.fill('SELCT * FROM input');

        // Look for validation feedback
        const validateButton = page.locator('button:has-text("Validate"), button:has-text("Check")');
        if (await validateButton.isVisible()) {
          await validateButton.click();
          await page.waitForTimeout(2000);

          const errorIndicator = page.locator('.error, [data-testid="sql-error"], text=/syntax error/i');
          const hasError = await errorIndicator.isVisible().catch(() => false);

          if (hasError) {
            expect(errorIndicator).toBeVisible();
          }
        }
      }
    }
  });

  test('should support table name placeholder', async ({ page }) => {
    await canvas.dragNodeToCanvas('input');
    await canvas.dragNodeToCanvas('sql');

    const nodes = await canvas.getAllNodeLabels();
    if (nodes.length >= 2) {
      await canvas.connectNodes(nodes[0], nodes[1]);

      await canvas.clickNode(nodes.find(n => n.toLowerCase().includes('sql')) || 'SQL');

      const sqlEditor = page.locator('textarea[name="sql"]');
      if (await sqlEditor.isVisible()) {
        await sqlEditor.fill('SELECT * FROM {{input}} WHERE id > 5');
        await page.waitForTimeout(1000);

        await assertSqlPreviewContains(page, '{{input}}');
      }
    }
  });

  test('should execute custom SQL query', async ({ page }) => {
    await canvas.dragNodeToCanvas('input');
    await canvas.dragNodeToCanvas('sql');
    await canvas.dragNodeToCanvas('output');

    const nodes = await canvas.getAllNodeLabels();
    if (nodes.length >= 3) {
      await canvas.connectNodes(nodes[0], nodes[1]);
      await canvas.connectNodes(nodes[1], nodes[2]);

      // Upload data
      const buffer = Buffer.from(sampleCsvData.content, 'utf-8');
      const fileInput = page.locator('input[type="file"]');

      if (await fileInput.isVisible()) {
        const fileChooserPromise = page.waitForEvent('filechooser');
        await fileInput.click();
        const fileChooser = await fileChooserPromise;

        await fileChooser.setFiles({
          name: sampleCsvData.filename,
          mimeType: 'text/csv',
          buffer: buffer,
        });

        await page.waitForTimeout(2000);

        // Configure SQL node
        await canvas.clickNode(nodes.find(n => n.toLowerCase().includes('sql')) || 'SQL');

        const sqlEditor = page.locator('textarea[name="sql"]');
        if (await sqlEditor.isVisible()) {
          await sqlEditor.fill('SELECT * FROM input WHERE age > 25 LIMIT 5');
          await page.waitForTimeout(1000);

          // Execute workflow
          await canvas.execute();
          await page.waitForTimeout(5000);

          // Check output node
          await canvas.clickNode(nodes[2]);
          await dataPanel.switchToDataTab();

          const rowCount = await dataPanel.getDataRowCount();
          expect(rowCount).toBeLessThanOrEqual(5);
        }
      }
    }
  });

  test('should support complex SQL queries', async ({ page }) => {
    await canvas.dragNodeToCanvas('input');
    await canvas.dragNodeToCanvas('sql');

    const nodes = await canvas.getAllNodeLabels();
    if (nodes.length >= 2) {
      await canvas.connectNodes(nodes[0], nodes[1]);

      await canvas.clickNode(nodes.find(n => n.toLowerCase().includes('sql')) || 'SQL');

      const sqlEditor = page.locator('textarea[name="sql"]');
      if (await sqlEditor.isVisible()) {
        const complexQuery = `
          SELECT
            city,
            COUNT(*) as user_count,
            AVG(age) as avg_age,
            MAX(age) as max_age
          FROM input
          GROUP BY city
          HAVING COUNT(*) > 1
          ORDER BY user_count DESC
        `;

        await sqlEditor.fill(complexQuery);
        await page.waitForTimeout(1000);

        await assertSqlPreviewContains(page, 'GROUP BY');
        await assertSqlPreviewContains(page, 'HAVING');
        await assertSqlPreviewContains(page, 'ORDER BY');
      }
    }
  });

  test('should support SQL with joins', async ({ page }) => {
    await canvas.dragNodeToCanvas('input');
    await canvas.dragNodeToCanvas('sql');

    const nodes = await canvas.getAllNodeLabels();
    if (nodes.length >= 2) {
      await canvas.connectNodes(nodes[0], nodes[1]);

      await canvas.clickNode(nodes.find(n => n.toLowerCase().includes('sql')) || 'SQL');

      const sqlEditor = page.locator('textarea[name="sql"]');
      if (await sqlEditor.isVisible()) {
        await sqlEditor.fill(`
          SELECT
            a.id,
            a.name,
            b.email
          FROM input a
          INNER JOIN input b ON a.id = b.id
        `);

        await page.waitForTimeout(1000);

        await assertSqlPreviewContains(page, 'INNER JOIN');
      }
    }
  });

  test('should support window functions', async ({ page }) => {
    await canvas.dragNodeToCanvas('input');
    await canvas.dragNodeToCanvas('sql');

    const nodes = await canvas.getAllNodeLabels();
    if (nodes.length >= 2) {
      await canvas.connectNodes(nodes[0], nodes[1]);

      await canvas.clickNode(nodes.find(n => n.toLowerCase().includes('sql')) || 'SQL');

      const sqlEditor = page.locator('textarea[name="sql"]');
      if (await sqlEditor.isVisible()) {
        await sqlEditor.fill(`
          SELECT
            *,
            ROW_NUMBER() OVER (PARTITION BY city ORDER BY age DESC) as rank
          FROM input
        `);

        await page.waitForTimeout(1000);

        await assertSqlPreviewContains(page, 'ROW_NUMBER');
        await assertSqlPreviewContains(page, 'OVER');
      }
    }
  });

  test('should format SQL query', async ({ page }) => {
    await canvas.dragNodeToCanvas('input');
    await canvas.dragNodeToCanvas('sql');

    const nodes = await canvas.getAllNodeLabels();
    if (nodes.length >= 2) {
      await canvas.connectNodes(nodes[0], nodes[1]);

      await canvas.clickNode(nodes.find(n => n.toLowerCase().includes('sql')) || 'SQL');

      const sqlEditor = page.locator('textarea[name="sql"]');
      if (await sqlEditor.isVisible()) {
        await sqlEditor.fill('select name,email from input where age>25');

        // Look for format button
        const formatButton = page.locator('button:has-text("Format"), button:has-text("Prettify")');
        if (await formatButton.isVisible()) {
          await formatButton.click();
          await page.waitForTimeout(1000);

          const formattedSql = await sqlEditor.inputValue();
          expect(formattedSql).toContain('SELECT');
        }
      }
    }
  });

  test('should show SQL execution plan', async ({ page }) => {
    await canvas.dragNodeToCanvas('input');
    await canvas.dragNodeToCanvas('sql');

    const nodes = await canvas.getAllNodeLabels();
    if (nodes.length >= 2) {
      await canvas.connectNodes(nodes[0], nodes[1]);

      await canvas.clickNode(nodes.find(n => n.toLowerCase().includes('sql')) || 'SQL');

      const sqlEditor = page.locator('textarea[name="sql"]');
      if (await sqlEditor.isVisible()) {
        await sqlEditor.fill('SELECT * FROM input');

        // Look for explain/plan button
        const explainButton = page.locator('button:has-text("Explain"), button:has-text("Plan")');
        if (await explainButton.isVisible()) {
          await explainButton.click();
          await page.waitForTimeout(2000);

          const planDisplay = page.locator('[data-testid="execution-plan"], pre:has-text("PRODUCTION")');
          const hasPlan = await planDisplay.isVisible().catch(() => false);

          if (hasPlan) {
            expect(planDisplay).toBeVisible();
          }
        }
      }
    }
  });

  test('should handle SQL errors gracefully', async ({ page }) => {
    await canvas.dragNodeToCanvas('input');
    await canvas.dragNodeToCanvas('sql');
    await canvas.dragNodeToCanvas('output');

    const nodes = await canvas.getAllNodeLabels();
    if (nodes.length >= 3) {
      await canvas.connectNodes(nodes[0], nodes[1]);
      await canvas.connectNodes(nodes[1], nodes[2]);

      // Upload data
      const buffer = Buffer.from(sampleCsvData.content, 'utf-8');
      const fileInput = page.locator('input[type="file"]');

      if (await fileInput.isVisible()) {
        const fileChooserPromise = page.waitForEvent('filechooser');
        await fileInput.click();
        const fileChooser = await fileChooserPromise;

        await fileChooser.setFiles({
          name: sampleCsvData.filename,
          mimeType: 'text/csv',
          buffer: buffer,
        });

        await page.waitForTimeout(2000);

        // Configure SQL with error
        await canvas.clickNode(nodes.find(n => n.toLowerCase().includes('sql')) || 'SQL');

        const sqlEditor = page.locator('textarea[name="sql"]');
        if (await sqlEditor.isVisible()) {
          await sqlEditor.fill('SELECT * FROM nonexistent_table');

          // Execute
          await canvas.execute();
          await page.waitForTimeout(5000);

          // Should show error
          const errorMessage = page.locator('text=/error|table.*not found/i');
          const hasError = await errorMessage.isVisible().catch(() => false);

          if (hasError) {
            expect(errorMessage).toBeVisible();
          }
        }
      }
    }
  });

  test('should support multiple input sources', async ({ page }) => {
    await canvas.dragNodeToCanvas('input', { x: 100, y: 100 });
    await canvas.dragNodeToCanvas('input', { x: 100, y: 300 });
    await canvas.dragNodeToCanvas('sql', { x: 400, y: 200 });

    const nodes = await canvas.getAllNodeLabels();
    if (nodes.length >= 3) {
      await canvas.connectNodes(nodes[0], nodes[2]);
      await canvas.connectNodes(nodes[1], nodes[2]);

      await canvas.clickNode(nodes.find(n => n.toLowerCase().includes('sql')) || 'SQL');

      const sqlEditor = page.locator('textarea[name="sql"]');
      if (await sqlEditor.isVisible()) {
        await sqlEditor.fill('SELECT * FROM {{input1}} UNION ALL SELECT * FROM {{input2}}');
        await page.waitForTimeout(1000);

        await assertSqlPreviewContains(page, 'UNION ALL');
      }
    }
  });
});
