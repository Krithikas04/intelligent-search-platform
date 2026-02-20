// @ts-check
const { defineConfig, devices } = require('@playwright/test')

module.exports = defineConfig({
  testDir: './tests',
  timeout: 60_000,
  retries: 0,
  workers: 1,        // serial execution avoids hitting the 10/min login rate limit
  reporter: 'list',
  use: {
    baseURL: 'http://localhost:5173',
    headless: false,          // set true for CI
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
})
