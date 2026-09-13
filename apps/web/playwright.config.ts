import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './browser',
  outputDir: '../../test-results/browser',
  use: { baseURL: process.env.API_BASE_URL ?? 'http://127.0.0.1:8000', trace: 'retain-on-failure' },
  projects: [
    { name: 'desktop', use: { browserName: 'chromium', viewport: { width: 1440, height: 1000 } } },
    { name: 'mobile', use: { browserName: 'chromium', viewport: { width: 390, height: 844 } } },
    { name: 'narrow', use: { browserName: 'chromium', viewport: { width: 320, height: 740 } } },
  ],
});
