import { test, expect } from '@playwright/test';

test.describe('Mobile Bottom Sheet Scroll Diagnostic', () => {
  test('minimal scroll test with direct DOM manipulation', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');

    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(500);

    // Create a minimal test bottom sheet with the exact same structure as the real one
    await page.evaluate(() => {
      // Create bottom sheet container - use !important to ensure styles take effect
      const bottomSheet = document.createElement('div');
      bottomSheet.id = 'test-bottom-sheet'; // Unique ID to select the right element
      bottomSheet.className = 'fixed inset-x-0 bottom-0 z-50 bg-white rounded-t-2xl shadow-2xl border-t border-[#DFE1E6]';
      bottomSheet.style.cssText = 'height: 70vh !important; display: flex !important; flex-direction: column !important;';

      // Create scrollable content area with overflow-y-auto
      const scrollableContent = document.createElement('div');
      scrollableContent.className = 'overflow-y-auto';
      scrollableContent.style.padding = '16px';
      scrollableContent.style.overflowY = 'auto';
      scrollableContent.style.setProperty('flex', '1 1 auto', 'important'); // Use setProperty for !important
      scrollableContent.style.WebkitOverflowScrolling = 'touch'; // iOS momentum scrolling

      // Add enough content to require scrolling
      let contentHTML = '<div style="padding: 16px;">';
      for (let i = 0; i < 50; i++) {
        contentHTML += `<div class="p-4 bg-gray-50 mb-2 rounded" style="height: 60px;">Test line ${i + 1}</div>`;
      }
      contentHTML += '</div>';

      scrollableContent.innerHTML = contentHTML;
      bottomSheet.appendChild(scrollableContent);
      document.body.appendChild(bottomSheet);
    });

    await page.waitForTimeout(500);

    // Test 1: Verify the element exists and is scrollable
    const scrollTest = await page.evaluate(() => {
      // Only select the scrollable content within our test bottom sheet
      const bottomSheet = document.querySelector('#test-bottom-sheet');
      if (!bottomSheet) return { error: 'Test bottom sheet not found' };

      const scrollable = bottomSheet.querySelector('.overflow-y-auto');
      if (!scrollable) return { error: 'Scrollable element not found' };

      const el = scrollable as HTMLElement;
      const parent = el.parentElement;

      return {
        canScroll: el.scrollHeight > el.clientHeight,
        scrollHeight: el.scrollHeight,
        clientHeight: el.clientHeight,
        offsetHeight: el.offsetHeight,
        overflowY: window.getComputedStyle(el).overflowY,
        webkitOverflowScrolling: window.getComputedStyle(el).webkitOverflowScrolling,
        touchAction: window.getComputedStyle(el).touchAction,
        parentDisplay: parent ? window.getComputedStyle(parent).display : null,
        parentFlexDirection: parent ? window.getComputedStyle(parent).flexDirection : null,
        parentHeight: parent ? parent.offsetHeight : null,
        elFlex: window.getComputedStyle(el).flex
      };
    });

    console.log('Scroll test results:', scrollTest);

    // Check for styles that might block scrolling
    const scrollBlockCheck = await page.evaluate(() => {
      const bottomSheet = document.querySelector('#test-bottom-sheet');
      if (!bottomSheet) return { error: 'Test bottom sheet not found' };

      const scrollable = bottomSheet.querySelector('.overflow-y-auto') as HTMLElement;

      return {
        scrollableTouchAction: window.getComputedStyle(scrollable).touchAction,
        scrollableOverflowY: window.getComputedStyle(scrollable).overflowY,
        scrollableOverflowX: window.getComputedStyle(scrollable).overflowX,
        scrollableWebkitOverflow: (scrollable.style as any).WebkitOverflowScrolling,
        parentTouchAction: window.getComputedStyle(bottomSheet).touchAction,
        scrollTopWorks: (() => {
          const before = scrollable.scrollTop;
          scrollable.scrollTop = 100;
          return scrollable.scrollTop > before;
        })()
      };
    });

    console.log('Scroll block check:', scrollBlockCheck);

    // The element should now have actual dimensions with height: 70vh
    if (scrollTest.clientHeight === 0) {
      console.log('WARNING: Element still has 0 height. Checking bottom sheet...');
      const bottomSheetDebug = await page.evaluate(() => {
        const bottomSheet = document.querySelector('#test-bottom-sheet');
        if (!bottomSheet) return { error: 'Bottom sheet not found' };
        const el = bottomSheet as HTMLElement;
        return {
          offsetHeight: el.offsetHeight,
          clientHeight: el.clientHeight,
          computedHeight: window.getComputedStyle(el).height,
          display: window.getComputedStyle(el).display,
          flexDirection: window.getComputedStyle(el).flexDirection
        };
      });
      console.log('Bottom sheet debug:', bottomSheetDebug);
    }

    expect(scrollTest.canScroll).toBe(true);

    // Test 2: Try to scroll using JavaScript
    const scrollBefore = await page.evaluate(() => {
      const bottomSheet = document.querySelector('#test-bottom-sheet');
      if (!bottomSheet) return -999;
      const el = bottomSheet.querySelector('.overflow-y-auto') as HTMLElement;
      return el.scrollTop;
    });

    await page.evaluate(() => {
      const bottomSheet = document.querySelector('#test-bottom-sheet');
      if (!bottomSheet) return;
      const el = bottomSheet.querySelector('.overflow-y-auto') as HTMLElement;
      el.scrollTop = 200; // Scroll further
    });

    const scrollAfter = await page.evaluate(() => {
      const bottomSheet = document.querySelector('#test-bottom-sheet');
      if (!bottomSheet) return -999;
      const el = bottomSheet.querySelector('.overflow-y-auto') as HTMLElement;
      return el.scrollTop;
    });

    console.log('Scroll before:', scrollBefore, 'after:', scrollAfter);
    expect(scrollAfter).toBeGreaterThanOrEqual(scrollBefore);

    // Test 3: Simulate touch scroll (if possible)
    const touchScrollTest = await page.evaluate(() => {
      const el = document.querySelector('.overflow-y-auto') as HTMLElement;

      // Record initial position
      const initialScroll = el.scrollTop;

      // Try to trigger scroll by dispatching touch events
      const touchStart = new TouchEvent('touchstart', {
        bubbles: true,
        touches: [{ clientX: 100, clientY: 100, identifier: 0, target: el, force: 1, radiusX: 1, radiusY: 1, rotationAngle: 0 } as any]
      });

      const touchMove = new TouchEvent('touchmove', {
        bubbles: true,
        touches: [{ clientX: 100, clientY: 50, identifier: 0, target: el, force: 1, radiusX: 1, radiusY: 1, rotationAngle: 0 } as any],
        cancelable: true
      });

      el.dispatchEvent(touchStart);
      el.dispatchEvent(touchMove);

      return {
        initialScroll,
        finalScroll: el.scrollTop,
        scrollChanged: el.scrollTop > initialScroll
      };
    });

    console.log('Touch scroll test:', touchScrollTest);
  });
});
