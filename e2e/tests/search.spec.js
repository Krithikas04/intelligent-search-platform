// @ts-check
const { test, expect } = require('@playwright/test')

const BASE = 'http://localhost:5173'
const SEARCH_PLACEHOLDER = 'Ask anything about your training materials or performance...'

// ── Helpers ───────────────────────────────────────────────────────────────────

async function login(page, username = 'frank-hexaloom') {
  await page.goto(BASE)
  await page.locator('#username').fill(username)
  await page.locator('#password').fill('demo1234')
  await page.getByRole('button', { name: 'Sign in' }).click()
  await expect(page.getByPlaceholder(SEARCH_PLACEHOLDER)).toBeVisible({ timeout: 10_000 })
}

async function search(page, query, mode = 'auto') {
  const input = page.getByPlaceholder(SEARCH_PLACEHOLDER)
  await input.fill(query)
  // Mode is a <select> element
  await page.locator('select').selectOption(mode)
  await page.getByRole('button', { name: 'Search' }).click()
  // Wait for the answer card to appear (data-testid added to AnswerCard)
  await expect(page.getByTestId('answer-card')).toBeVisible({ timeout: 30_000 })
}

// ── User sets ─────────────────────────────────────────────────────────────────

// > 2 users for general UI / mode-switching tests
const GENERAL_USERS = [
  { username: 'frank-hexaloom',  hasPlays: true  },
  { username: 'edward-hexaloom', hasPlays: true  },
  { username: 'alice-veldra',    hasPlays: false },
]

// > 5 users for answers / response-tier tests
// hasPlays drives whether knowledge search returns grounded results:
//   users with no plays get Tier 3 ("No Results Found") by design (retriever.py:83)
const ANSWER_USERS = [
  { username: 'frank-hexaloom',    hasPlays: true,  knowledgeQuery: 'Tell me about Hexenon material'    },
  { username: 'edward-hexaloom',   hasPlays: true,  knowledgeQuery: 'Tell me about Hexenon material'    },
  { username: 'alice-veldra',      hasPlays: false, knowledgeQuery: 'Tell me about Amproxin antibiotic' },
  { username: 'aaron-veldra',      hasPlays: true,  knowledgeQuery: 'Tell me about Amproxin antibiotic' },
  { username: 'beatrice-aetheris', hasPlays: false, knowledgeQuery: 'Tell me about Somnirel'            },
  { username: 'amy-kyberon',       hasPlays: false, knowledgeQuery: 'Tell me about GridMaster'          },
]

// ── Tests ─────────────────────────────────────────────────────────────────────

test.describe('Search — UI', () => {
  for (const u of GENERAL_USERS) {
    test.describe(`[${u.username}]`, () => {
      test.beforeEach(async ({ page }) => {
        await login(page, u.username)
      })

      test('search bar and mode selector are visible', async ({ page }) => {
        await expect(page.getByPlaceholder(SEARCH_PLACEHOLDER)).toBeVisible()
        const modeSelect = page.locator('select')
        await expect(modeSelect).toBeVisible()
        await expect(modeSelect.locator('option[value="auto"]')).toHaveCount(1)
        await expect(modeSelect.locator('option[value="knowledge"]')).toHaveCount(1)
        await expect(modeSelect.locator('option[value="performance"]')).toHaveCount(1)
      })

      test('assigned plays panel visibility matches account', async ({ page }) => {
        if (u.hasPlays) {
          await expect(page.getByText('Your assigned training plays')).toBeVisible()
        } else {
          await expect(page.getByText('Your assigned training plays')).not.toBeVisible()
        }
      })

      test('suggestion button is visible and clickable', async ({ page }) => {
        // Suggestions are hardcoded in SearchPage.tsx — same for all users
        const btn = page.getByRole('button', { name: 'What are the key benefits of Amproxin?' })
        await expect(btn).toBeVisible()
        await btn.click()
        // Query is submitted directly — answer card should appear
        await expect(page.getByTestId('answer-card')).toBeVisible({ timeout: 30_000 })
      })

      test('character counter updates while typing', async ({ page }) => {
        const input = page.getByPlaceholder(SEARCH_PLACEHOLDER)
        await input.fill('hello')
        await expect(page.getByText('5/500')).toBeVisible()
      })
    })
  }
})

test.describe('Search — Response Tiers', () => {
  for (const u of ANSWER_USERS) {
    test.describe(`[${u.username}]`, () => {
      test.beforeEach(async ({ page }) => {
        await login(page, u.username)
      })

      test('knowledge query returns expected tier based on play assignment', async ({ page }) => {
        await search(page, u.knowledgeQuery, 'knowledge')
        const card = page.getByTestId('answer-card')
        if (u.hasPlays) {
          // Users with assigned plays have indexed content → Grounded Answer
          await expect(card.getByText('Grounded Answer')).toBeVisible({ timeout: 30_000 })
        } else {
          // Users with no plays → retriever returns [] immediately → Tier 3
          await expect(card.getByText('No Results Found')).toBeVisible({ timeout: 10_000 })
        }
      })

      test('out-of-scope query returns Out of Scope badge', async ({ page }) => {
        await search(page, 'What is the population of France?')
        // The intent badge and the answer-card badge both say "Out of Scope"; scope to answer-card
        await expect(page.getByTestId('answer-card').getByText('Out of Scope')).toBeVisible({ timeout: 30_000 })
      })

      test('general professional query returns General Knowledge badge', async ({ page }) => {
        await search(page, 'What are best practices for cold calling?')
        await expect(page.getByTestId('answer-card').getByText('General Knowledge')).toBeVisible({ timeout: 30_000 })
      })

      test('intent badge appears below search bar after response', async ({ page }) => {
        await search(page, 'Tell me about product training')
        await expect(page.getByText('Detected intent:')).toBeVisible({ timeout: 5_000 })
      })

      test('assigned plays panel hides after first search', async ({ page }) => {
        if (u.hasPlays) {
          // Visible before search only if user has plays
          await expect(page.getByText('Your assigned training plays')).toBeVisible()
        }
        await search(page, 'Tell me about products')
        // Should disappear once results are showing
        await expect(page.getByText('Your assigned training plays')).not.toBeVisible()
      })
    })
  }
})

test.describe('Search — Mode Switching', () => {
  for (const u of GENERAL_USERS) {
    test.describe(`[${u.username}]`, () => {
      test.beforeEach(async ({ page }) => {
        await login(page, u.username)
      })

      test('switching to performance mode and searching', async ({ page }) => {
        await search(page, 'Show my submission scores', 'performance')
        await expect(page.getByTestId('answer-card')).toBeVisible({ timeout: 30_000 })
      })

      test('switching to knowledge mode forces knowledge search', async ({ page }) => {
        await search(page, 'Product overview', 'knowledge')
        // Should get grounded or tier3, not out_of_scope or general
        const card = page.getByTestId('answer-card')
        await expect(card).toBeVisible({ timeout: 30_000 })
        const text = await card.innerText()
        expect(text).not.toMatch(/out of scope/i)
      })
    })
  }
})
