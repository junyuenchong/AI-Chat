/**
 * Auth API — register, login, logout, current user.
 *
 * Request path:
 *   features/auth/AuthProvider.tsx
 *     → features/auth/api.ts  (this file)
 *     → lib/api/client.ts → FastAPI /api/v1/auth/*
 */

import { apiJson, apiUrl, authHeaders, readError } from "@/lib/api/client";
import { clearAccessToken, getAccessToken, setAccessToken } from "@/lib/auth/token";

import type { TokenResponse, UserProfile } from "./types";

// ────────────────────────────────────────────────────────
// registerUser
// Path: features/auth/api.ts
// Endpoint: POST /auth/register
// Use: create account and store JWT in sessionStorage.
// ────────────────────────────────────────────────────────
export async function registerUser(body: {
  email: string;
  password: string;
  name: string;
}): Promise<TokenResponse> {
  // Step 1 — call register endpoint.
  const token = await apiJson<TokenResponse>("/api/v1/auth/register", {
    method: "POST",
    body: JSON.stringify(body),
  });
  // Step 2 — save JWT for subsequent requests.
  setAccessToken(token.access_token);
  return token;
}

// ────────────────────────────────────────────────────────
// loginUser
// Path: features/auth/api.ts
// Endpoint: POST /auth/login
// Use: sign in and store JWT in sessionStorage.
// ────────────────────────────────────────────────────────
export async function loginUser(body: {
  email: string;
  password: string;
}): Promise<TokenResponse> {
  const token = await apiJson<TokenResponse>("/api/v1/auth/login", {
    method: "POST",
    body: JSON.stringify(body),
  });
  setAccessToken(token.access_token);
  return token;
}

// ────────────────────────────────────────────────────────
// logoutUser
// Path: features/auth/api.ts
// Use: clear JWT client-side (stateless JWT — no server call).
// ────────────────────────────────────────────────────────
export async function logoutUser(): Promise<void> {
  clearAccessToken();
}

// ────────────────────────────────────────────────────────
// fetchCurrentUser
// Path: features/auth/api.ts
// Endpoint: GET /auth/me
// Use: restore session on page load when a token exists.
// ────────────────────────────────────────────────────────
export async function fetchCurrentUser(): Promise<UserProfile | null> {
  // Step 1 — skip network call when not logged in.
  const token = getAccessToken();
  if (!token) return null;

  const res = await fetch(apiUrl("/api/v1/auth/me"), {
    headers: authHeaders(token),
  });
  // Step 2 — stale or invalid token → clear and treat as logged out.
  if (res.status === 401) {
    clearAccessToken();
    return null;
  }
  if (!res.ok) {
    throw new Error(await readError(res, "Request failed"));
  }
  return (await res.json()) as UserProfile;
}
