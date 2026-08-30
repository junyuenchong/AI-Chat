/**
 * JWT token storage for Q2 auth.
 *
 * Request path:
 *   features/auth/api.ts
 *     → lib/auth/token.ts  (this file)
 *     → sessionStorage
 */

const TOKEN_KEY = "ai_chat_access_token";

// ────────────────────────────────────────────────────────
// getAccessToken
// Path: lib/auth/token.ts
// Use: read JWT from sessionStorage (client-only).
// ────────────────────────────────────────────────────────
export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return sessionStorage.getItem(TOKEN_KEY);
}

// ────────────────────────────────────────────────────────
// setAccessToken
// Path: lib/auth/token.ts
// Endpoint: POST /auth/login, POST /auth/register
// Use: persist JWT after successful auth.
// ────────────────────────────────────────────────────────
export function setAccessToken(token: string): void {
  sessionStorage.setItem(TOKEN_KEY, token);
}

// ────────────────────────────────────────────────────────
// clearAccessToken
// Path: lib/auth/token.ts
// Use: logout or clear stale token after 401.
// ────────────────────────────────────────────────────────
export function clearAccessToken(): void {
  sessionStorage.removeItem(TOKEN_KEY);
}
