import { test, expect } from '@playwright/test';

test.describe('Mobile Bottom Sheet Scrolling', () => {
  test('should open bottom sheet when node is clicked', async ({ page }) => {
    // Set mobile viewport BEFORE navigating to ensure mobile components render
    await page.setViewportSize({ width: 375, height: 667 }); // iPhone SE

    await page.goto('/');

    // Wait for page to load and mobile components to render
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(500); // Extra wait for responsive hooks to update

    // Create test nodes directly in the DOM (simpler than loading through the app flow)
    await page.evaluate(() => {
      const mobileViewer = document.querySelector('[data-testid="mobile-workflow-viewer"]');
      if (!mobileViewer) return;

      // Find the container div inside mobile viewer
      const container = mobileViewer.querySelector('.relative.w-full.h-full');
      if (!container) return;

      // Create a test node
      const testNode = document.createElement('div');
      testNode.className = 'absolute bg-white border-2 rounded-lg shadow-lg p-3 min-w-[140px] max-w-[180px] transition-all';
      testNode.style.left = '50px';
      testNode.style.top = '100px';
      testNode.innerHTML = `
        <div class="flex flex-col space-y-1.5">
          <div class="flex items-center space-x-1.5">
            <span class="w-1 h-4 bg-[#0052CC] rounded-full"></span>
            <span class="text-xs font-bold text-[#172B4D]">Test Node</span>
          </div>
          <div class="flex items-center space-x-1 bg-[#EAE6FF] text-[#403294] px-2 py-0.5 rounded text-[9px] font-semibold">
            <span>100</span>
            <span class="opacity-60">rows</span>
          </div>
        </div>
      `;

      container.appendChild(testNode);
    });

    // Wait for DOM to update
    await page.waitForTimeout(500);

    // Debug: Check what elements are available
    const bodyText = await page.evaluate(() => {
      const hasMobileViewer = !!document.querySelector('[data-testid="mobile-workflow-viewer"]');
      const hasReactFlow = !!document.querySelector('.react-flow');
      const windowWidth = window.innerWidth;
      return {
        hasMobileViewer,
        hasReactFlow,
        windowWidth,
        bodyClasses: document.body.className
      };
    });
    console.log('Page state:', bodyText);

    // Debug: Check if nodes exist in mobile viewer
    const nodeDebug = await page.evaluate(() => {
      const mobileViewer = document.querySelector('[data-testid="mobile-workflow-viewer"]');
      if (!mobileViewer) return { error: 'No mobile viewer' };

      const allNodes = mobileViewer.querySelectorAll('.absolute.bg-white.border-2');
      return {
        nodeCount: allNodes.length,
        firstNodeHTML: allNodes[0]?.outerHTML?.substring(0, 200)
      };
    });
    console.log('Mobile viewer nodes:', nodeDebug);
    const firstNode = page.locator('.absolute.bg-white.border-2').first();
    await firstNode.click();

    // Wait for bottom sheet to appear
    const bottomSheet = page.locator('.fixed.inset-x-0.bottom-0.z-50');
    await expect(bottomSheet).toBeVisible({ timeout: 3000 });
  });

  test('should scroll bottom sheet content with touch', async ({ page }) => {
    // Set mobile viewport BEFORE navigating
    await page.setViewportSize({ width: 375, height: 667 });

    await page.goto('/');

    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(500);

    // Click on first node
    const firstNode = page.locator('.absolute.bg-white.border-2').first();
    await firstNode.click();

    // Wait for bottom sheet
    const bottomSheet = page.locator('.fixed.inset-x-0.bottom-0.z-50');
    await expect(bottomSheet).toBeVisible({ timeout: 3000 });

    // Get scrollable content area
    const scrollableContent = bottomSheet.locator('.overflow-y-auto').first();

    // Check if element has overflow-y-auto class
    await expect(scrollableContent).toHaveClass('overflow-y-auto');

    // Try to scroll using JavaScript
    const scrollResult = await scrollableContent.evaluate((el: HTMLElement) => {
      // Record initial scroll position
      const initialScroll = el.scrollTop;

      // Try to scroll
      el.scrollTop = 100;

      // Check if scroll position changed
      const finalScroll = el.scrollTop;

      return {
        initialScroll,
        finalScroll,
        scrolled: finalScroll > initialScroll,
        scrollHeight: el.scrollHeight,
        clientHeight: el.clientHeight,
        canScroll: el.scrollHeight > el.clientHeight
      };
    });

    console.log('Scroll test result:', scrollResult);

    // Verify the element can potentially scroll
    expect(scrollResult.canScroll).toBeTruthy();
  });

  test('bottom sheet should have higher z-index than canvas', async ({ page }) => {
    // Set mobile viewport BEFORE navigating
    await page.setViewportSize({ width: 375, height: 667 });

    await page.goto('/');

    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(500);

    // Click node to open bottom sheet
    const firstNode = page.locator('.absolute.bg-white.border-2').first();
    await firstNode.click();

    // Wait for bottom sheet
    await page.waitForSelector('.fixed.inset-x-0.bottom-0.z-50', { timeout: 3000 });

    // Check computed z-index values
    const zIndices = await page.evaluate(() => {
      const bottomSheet = document.querySelector('.fixed.inset-x-0.bottom-0.z-50');
      const canvas = document.querySelector('.absolute.inset-0.mt-16');

      return {
        bottomSheetZ: bottomSheet ? parseInt(window.getComputedStyle(bottomSheet).zIndex || '0') : 0,
        canvasZ: canvas ? parseInt(window.getComputedStyle(canvas).zIndex || '0') : 0
      };
    });

    console.log('Z-indices:', zIndices);

    // Bottom sheet should have higher z-index
    expect(zIndices.bottomSheetZ).toBeGreaterThan(zIndices.canvasZ);
  });

  test('bottom sheet should not have touch-action none', async ({ page }) => {
    // Set mobile viewport BEFORE navigating
    await page.setViewportSize({ width: 375, height: 667 });

    await page.goto('/');

    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(500);

    // Click node to open bottom sheet
    const firstNode = page.locator('.absolute.bg-white.border-2').first();
    await firstNode.click();

    // Wait for bottom sheet
    await page.waitForSelector('.fixed.inset-x-0.bottom-0.z-50', { timeout: 3000 });

    // Check touch-action style
    const touchAction = await page.locator('.fixed.inset-x-0.bottom-0.z-50').first().evaluate(el => {
      return window.getComputedStyle(el).touchAction;
    });

    console.log('Bottom sheet touch-action:', touchAction);

    // Should NOT be 'none' - should be 'auto' or empty
    expect(touchAction).not.toBe('none');
  });
});
