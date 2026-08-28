/**
 * E2E — knowledge base user flow (upload document, see it in list).
 */

import { test, expect } from "@playwright/test";

import { isBackendReady, registerAndLogin, uniqueEmail } from "./helpers";

// ────────────────────────────────────────────────────────────
// knowledge flow
// Feature: knowledge
// Endpoint: GET /documents, POST /documents
// Use: verify upload form → API → document appears in the list.
// ────────────────────────────────────────────────────────────

test.describe("knowledge", () => {
  test.beforeEach(async ({ request }) => {
    const ready = await isBackendReady(request);
    test.skip(!ready, "FastAPI backend is not running on localhost:8000");
  });

  test("user can upload a document and see it listed", async ({ page }) => {
    const email = uniqueEmail("knowledge");
    await registerAndLogin(page, email);

    const filename = `policy-${Date.now()}.md`;
    const content = "Annual leave: 14 days per year.";

    await page.getByRole("link", { name: /knowledge/i }).click();
    await expect(page).toHaveURL(/\/knowledge/);

    await page.getByPlaceholder(/filename/i).fill(filename);
    await page.getByPlaceholder(/paste knowledge/i).fill(content);
    await page.getByRole("button", { name: /^upload$/i }).click();

    // Document row appears after successful upload and list refresh.
    await expect(page.getByText(filename)).toBeVisible({ timeout: 15_000 });
  });
});
