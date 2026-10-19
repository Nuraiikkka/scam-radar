import { defineConfig } from '@playwright/test';

const channel = process.env.E2E_CHANNEL || undefined;

export default defineConfig({
  testDir: './tests',
  timeout: 8 * 60 * 1000,
  expect: { timeout: 20 * 1000 },
  workers: 1,
  retries: 0,
  reporter: [['list'], ['html', { open: 'never', outputFolder: 'report' }]],
  use: {
    baseURL: process.env.E2E_BASE_URL || 'http://localhost:8080',
    channel,
    headless: true,
    viewport: { width: 412, height: 915 },
    locale: 'en-US',
    actionTimeout: 20 * 1000,
    trace: 'retain-on-failure',
    video: 'retain-on-failure',
  },
});
