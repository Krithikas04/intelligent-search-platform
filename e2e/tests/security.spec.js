// @ts-check
const { test, expect } = require('@playwright/test')

const BASE = 'http://localhost:5173'
const SEARCH_PLACEHOLDER = 'Ask anything about your training materials or performance...'

/**
 * Security isolation tests.
 * Verifies company-level data isolation and auth token integrity.
 */

async function loginAs(page, username) {
  await page.goto(BASE)
  await page.locator('#username').fill(username)
  await page.locator('#password').fill('demo1234')
  await page.getByRole('button', { name: 'Sign in' }).click()
  await expect(page.getByPlaceholder(SEARCH_PLACEHOLDER)).toBeVisible({ timeout: 10_000 })
}

// ── Tests ─────────────────────────────────────────────────────────────────────

test.describe('Security — Company Isolation', () => {
  test('Veldra user sees Veldra in header, not Aetheris', async ({ page }) => {
    await loginAs(page, 'alice-veldra')
    // Header shows company_name from /auth/me
    await expect(page.getByText('Veldra Therapeutics')).toBeVisible()
    await expect(page.getByText('Aetheris Pharma')).not.toBeVisible()
  })

  test('Aetheris user sees Aetheris in header, not Veldra', async ({ page }) => {
    await loginAs(page, 'beatrice-aetheris')
    await expect(page.getByText('Aetheris Pharma')).toBeVisible()
    await expect(page.getByText('Veldra Therapeutics')).not.toBeVisible()
  })

  test('Veldra user answer does not mention Aetheris content', async ({ page }) => {
    await loginAs(page, 'alice-veldra')
    await page.getByPlaceholder(SEARCH_PLACEHOLDER).fill('Tell me about products')
    await page.locator('select').selectOption('knowledge')
    await page.getByRole('button', { name: 'Search' }).click()
    await expect(page.getByTestId('answer-card')).toBeVisible({ timeout: 30_000 })
    const text = await page.getByTestId('answer-card').innerText()
    expect(text.toLowerCase()).not.toContain('aetheris')
  })

  test('Aetheris user answer does not mention Veldra content', async ({ page }) => {
    await loginAs(page, 'beatrice-aetheris')
    await page.getByPlaceholder(SEARCH_PLACEHOLDER).fill('Tell me about products')
    await page.locator('select').selectOption('knowledge')
    await page.getByRole('button', { name: 'Search' }).click()
    await expect(page.getByTestId('answer-card')).toBeVisible({ timeout: 30_000 })
    const text = await page.getByTestId('answer-card').innerText()
    expect(text.toLowerCase()).not.toContain('veldra')
  })

  test('users from different companies see different assigned plays', async ({ browser }) => {
    // frank-hexaloom (Hexaloom Nanoworks) has 3 play assignments
    // alice-veldra (Veldra Therapeutics) has 0 play assignments
    // This demonstrates company-level data isolation
    const ctx1 = await browser.newContext()
    const ctx2 = await browser.newContext()
    const page1 = await ctx1.newPage()
    const page2 = await ctx2.newPage()

    await loginAs(page1, 'frank-hexaloom')
    await loginAs(page2, 'alice-veldra')

    // Hexaloom user sees their assigned plays panel
    await expect(page1.getByText('Your assigned training plays')).toBeVisible()
    // Veldra user has no assigned plays — panel is absent (different data from different company)
    await expect(page2.getByText('Your assigned training plays')).not.toBeVisible()

    await ctx1.close()
    await ctx2.close()
  })
})

test.describe('Security — Token Integrity', () => {
  test('no token → login page shown', async ({ page }) => {
    await page.goto(BASE)
    await page.evaluate(() => localStorage.clear())
    await page.reload()
    await expect(page.getByRole('heading', { name: 'Sign in to your account' })).toBeVisible()
  })

  test('tampered JWT → redirected to login', async ({ page }) => {
    await loginAs(page, 'alice-veldra')
    // Tamper with the stored token
    await page.evaluate(() => {
      const raw = localStorage.getItem('auth-store')
      if (raw) {
        const parsed = JSON.parse(raw)
        if (parsed?.state?.token) {
          parsed.state.token = 'eyJhbGciOiJIUzI1NiJ9.tampered.invalidsig'
          localStorage.setItem('auth-store', JSON.stringify(parsed))
        }
      }
    })
    await page.reload()
    // The /auth/me call will fail → logout → login page
    await expect(page.getByRole('heading', { name: 'Sign in to your account' })).toBeVisible({ timeout: 10_000 })
  })
})
