// @ts-check
const { test, expect } = require('@playwright/test')

const BASE = 'http://localhost:5173'
const VALID_USER = { username: 'alice-veldra', password: 'demo1234' }
const WRONG_PASS  = { username: 'alice-veldra', password: 'wrongpass' }
const BAD_USER    = { username: 'nobody-here',  password: 'demo1234' }

// ── Helpers ───────────────────────────────────────────────────────────────────

async function login(page, { username, password }) {
  await page.goto(BASE)
  await page.locator('#username').fill(username)
  await page.locator('#password').fill(password)
  await page.getByRole('button', { name: 'Sign in' }).click()
}

async function expectSearchPage(page) {
  await expect(
    page.getByPlaceholder('Ask anything about your training materials or performance...')
  ).toBeVisible({ timeout: 10_000 })
}

// ── Tests ─────────────────────────────────────────────────────────────────────

test.describe('Authentication', () => {
  test('shows login page when unauthenticated', async ({ page }) => {
    await page.goto(BASE)
    await expect(page.getByRole('heading', { name: 'Sign in to your account' })).toBeVisible()
    await expect(page.locator('#username')).toBeVisible()
    await expect(page.locator('#password')).toBeVisible()
    await expect(page.getByRole('button', { name: 'Sign in' })).toBeVisible()
  })

  test('successful login redirects to search page', async ({ page }) => {
    await login(page, VALID_USER)
    await expectSearchPage(page)
  })

  test('displays user name and company after login', async ({ page }) => {
    await login(page, VALID_USER)
    await expectSearchPage(page)
    await expect(page.getByText('Alice Johnson')).toBeVisible()
    await expect(page.getByText(/veldra/i)).toBeVisible()
  })

  test('wrong password shows error message', async ({ page }) => {
    await login(page, WRONG_PASS)
    await expect(page.getByText(/invalid credentials|login failed/i)).toBeVisible({ timeout: 10_000 })
  })

  test('unknown username shows error message', async ({ page }) => {
    await login(page, BAD_USER)
    await expect(page.getByText(/invalid credentials|login failed/i)).toBeVisible({ timeout: 10_000 })
  })

  test('sign out returns to login page', async ({ page }) => {
    await login(page, VALID_USER)
    await expectSearchPage(page)
    await page.getByRole('button', { name: 'Sign out' }).click()
    await expect(page.getByRole('heading', { name: 'Sign in to your account' })).toBeVisible({ timeout: 5_000 })
  })

  test('auth persists on page reload', async ({ page }) => {
    await login(page, VALID_USER)
    await expectSearchPage(page)
    await page.reload()
    // Token is stored in localStorage via Zustand persist — should still be on search page
    await expectSearchPage(page)
  })
})
