import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright configuration for DuckDB Web E2E tests
 */

const PORT = process.env.TEST_PORT || '3001';

export default defineConfig({
  testDir: '.',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1,
  reporter: [
    ['html', { outputFolder: 'playwright-report', open: 'never' }],
    ['json', { outputFile: 'test-results/results.json' }],
    ['junit', { outputFile: 'test-results/results.xml' }],
    ['list']
  ],
  use: {
    baseURL: `http://127.0.0.1:${PORT}`,
    trace: 'retain-on-failure',
    viewport: { width: 1920, height: 1080 },
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    actionTimeout: 10000,
    navigationTimeout: 30000,
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],

  webServer: {
    command: process.platform === 'win32' ? 'cmd /c ../../run.bat' : '../../run.sh',
    url: `http://127.0.0.1:${PORT}`,
    env: {
      PORT,
      PYTHONPATH: '.',
    },
    timeout: 300000,
    reuseExistingServer: true,  // Reuse existing server (for CI/pre-commit)
  },


  expect: {
    timeout: 5000,
  },
});
