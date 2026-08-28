/**
 * E2E — chat user flow (send message, receive streamed reply).
 */

import { test, expect } from "@playwright/test";

import { isBackendReady, registerAndLogin, uniqueEmail } from "./helpers";

// ────────────────────────────────────────────────────────────
// chat flow
// Feature: chat
// Endpoint: POST /chat/stream
// Use: verify UI → proxy → FastAPI SSE stream updates the message pane.
// ────────────────────────────────────────────────────────────

test.describe("chat", () => {
  test.beforeEach(async ({ request }) => {
    const ready = await isBackendReady(request);
    test.skip(!ready, "FastAPI backend is not running on localhost:8000");
  });

  test("user can send a message and see assistant reply", async ({ page }) => {
    const email = uniqueEmail("chat");
    await registerAndLogin(page, email);

    const composer = page.getByPlaceholder(/send a message/i);
    await composer.fill("Say hello in one word");
    await page.getByRole("button", { name: /^send$/i }).click();

    // User bubble appears immediately; assistant reply follows the stream.
    await expect(page.getByText("Say hello in one word")).toBeVisible({ timeout: 10_000 });
    // Wait until streaming finishes — Send button becomes enabled again.
    await expect(page.getByRole("button", { name: /^send$/i })).toBeEnabled({ timeout: 60_000 });
    // At least one assistant bubble with non-empty content (not just "Thinking…").
    const assistantBubbles = page.locator('[data-role="assistant"]');
    await expect(assistantBubbles.last()).not.toHaveText(/thinking/i, { timeout: 60_000 });
  });

  test("new chat button resets the conversation pane", async ({ page }) => {
    const email = uniqueEmail("newchat");
    await registerAndLogin(page, email);

    await page.getByRole("button", { name: /new chat/i }).click();
    await expect(page.getByText(/stack is up/i)).toBeVisible();
  });
});
