import { defineConfig } from '@playwright/test';

export default defineConfig({
  workers: 1,
  testDir: './browser',
  outputDir: process.env.PLAYWRIGHT_OUTPUT_DIR ?? '../../test-results/browser',
  use: {
    baseURL: process.env.API_BASE_URL ?? 'http://127.0.0.1:8000',
    trace: 'on',
    launchOptions: {
      // The Compose-only `api` hostname is HTTP and not localhost. Chromium
      // otherwise disables IndexedDB and crypto.randomUUID for this origin.
      args: ['--unsafely-treat-insecure-origin-as-secure=http://api:8000'],
    },
  },
  projects: [
    { name: 'desktop', use: { browserName: 'chromium', viewport: { width: 1440, height: 1000 } } },
    { name: 'mobile', use: { browserName: 'chromium', viewport: { width: 390, height: 844 } } },
    { name: 'small', use: { browserName: 'chromium', viewport: { width: 360, height: 780 } } },
    { name: 'narrow', use: { browserName: 'chromium', viewport: { width: 320, height: 740 } } },
  ],
});
