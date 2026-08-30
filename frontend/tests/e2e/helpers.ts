/**
 * Shared Playwright helpers for E2E flows.
 */

import type { APIRequestContext, Page } from "@playwright/test";

const API_BASE = process.env.PLAYWRIGHT_API_URL || "http://localhost:8000/api/v1";

// ────────────────────────────────────────────────────────────
// isBackendReady
// Feature: e2e helpers
// Endpoint: GET /health
// Use: skip E2E specs when FastAPI is not running.
// ────────────────────────────────────────────────────────────

export async function isBackendReady(request: APIRequestContext): Promise<boolean> {
  try {
    const res = await request.get(`${API_BASE}/health`, { timeout: 5_000 });
    return res.ok();
  } catch {
    return false;
  }
}

// ────────────────────────────────────────────────────────────
// uniqueEmail
// Feature: e2e helpers
// Use: generate a unique email so register tests do not collide.
// ────────────────────────────────────────────────────────────

export function uniqueEmail(prefix = "e2e"): string {
  return `${prefix}-${Date.now()}@example.com`;
}

// ────────────────────────────────────────────────────────────
// registerAndLogin
// Feature: e2e helpers
// Endpoint: POST /auth/register
// Use: register and log in via the UI before chat flows.
// ────────────────────────────────────────────────────────────

export async function registerAndLogin(
  page: Page,
  email: string,
  password = "secret123",
  name = "E2E User",
): Promise<void> {
  await page.goto("/register");
  await page.getByPlaceholder("Name").fill(name);
  await page.getByPlaceholder("Email").fill(email);
  await page.getByPlaceholder("Password").fill(password);
  await page.getByRole("button", { name: /register/i }).click();
  // Dashboard shell appears after successful registration.
  await page.getByRole("heading", { name: /ai chat/i }).waitFor({ timeout: 15_000 });
}
