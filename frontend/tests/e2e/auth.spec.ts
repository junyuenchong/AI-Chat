/**
 * E2E — authentication user flows (register, login, logout).
 */

import { test, expect } from "@playwright/test";

import { isBackendReady, uniqueEmail } from "./helpers";

// ────────────────────────────────────────────────────────────
// auth flows
// Feature: auth
// Endpoint: POST /auth/register, POST /auth/login, POST /auth/logout
// Use: verify real browser session cookie auth end-to-end.
// ────────────────────────────────────────────────────────────

test.describe("auth", () => {
  test.beforeEach(async ({ request }) => {
    const ready = await isBackendReady(request);
    test.skip(!ready, "FastAPI backend is not running on localhost:8000");
  });

  test("user can register and reach the chat dashboard", async ({ page }) => {
    const email = uniqueEmail("register");
    const password = "secret123";

    await page.goto("/register");
    await expect(page.getByRole("heading", { name: /create account/i })).toBeVisible();

    await page.getByPlaceholder("Name").fill("Playwright User");
    await page.getByPlaceholder("Email").fill(email);
    await page.getByPlaceholder("Password").fill(password);
    await page.getByRole("button", { name: /register/i }).click();

    // Authenticated shell: sidebar brand and user email.
    await expect(page.getByRole("heading", { name: /ai chat/i })).toBeVisible({
      timeout: 15_000,
    });
    await expect(page.getByText(email)).toBeVisible();
    await expect(page).toHaveURL(/\/chat/);
  });

  test("user can log out and return to login", async ({ page }) => {
    const email = uniqueEmail("logout");
    const password = "secret123";

    // Register first so we have a valid session.
    await page.goto("/register");
    await page.getByPlaceholder("Name").fill("Logout Test");
    await page.getByPlaceholder("Email").fill(email);
    await page.getByPlaceholder("Password").fill(password);
    await page.getByRole("button", { name: /register/i }).click();
    await page.getByRole("heading", { name: /ai chat/i }).waitFor({ timeout: 15_000 });

    await page.getByRole("button", { name: /log out/i }).click();
    await expect(page).toHaveURL(/\/login/, { timeout: 10_000 });
    await expect(page.getByRole("heading", { name: /sign in/i })).toBeVisible();
  });

  test("existing user can sign in from login page", async ({ page }) => {
    const email = uniqueEmail("login");
    const password = "secret123";

    // Create account via register UI.
    await page.goto("/register");
    await page.getByPlaceholder("Name").fill("Login Test");
    await page.getByPlaceholder("Email").fill(email);
    await page.getByPlaceholder("Password").fill(password);
    await page.getByRole("button", { name: /register/i }).click();
    await page.getByRole("heading", { name: /ai chat/i }).waitFor({ timeout: 15_000 });

    // Log out, then sign in again.
    await page.getByRole("button", { name: /log out/i }).click();
    await page.getByPlaceholder("Email").fill(email);
    await page.getByPlaceholder("Password").fill(password);
    await page.getByRole("button", { name: /sign in/i }).click();

    await expect(page.getByText(email)).toBeVisible({ timeout: 15_000 });
    await expect(page).toHaveURL(/\/chat/);
  });
});
