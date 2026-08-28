import { apiJson } from "@/lib/api/client";

import type { TokenResponse, UserProfile } from "./types";

// ────────────────────────────────────────────────────────
// registerUser
// Feature: auth
// Endpoint: POST /auth/register
// Use: create a new account and start a session.
// ────────────────────────────────────────────────────────

export async function registerUser(body: {
  email: string;
  password: string;
  name: string;
}): Promise<TokenResponse> {
  return apiJson<TokenResponse>("/api/v1/auth/register", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

// ────────────────────────────────────────────────────────
// loginUser
// Feature: auth
// Endpoint: POST /auth/login
// Use: authenticate and start a session.
// ────────────────────────────────────────────────────────

export async function loginUser(body: {
  email: string;
  password: string;
}): Promise<TokenResponse> {
  return apiJson<TokenResponse>("/api/v1/auth/login", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

// ────────────────────────────────────────────────────────
// logoutUser
// Feature: auth
// Endpoint: POST /auth/logout
// Use: revoke session and clear the HttpOnly cookie.
// ────────────────────────────────────────────────────────

export async function logoutUser(): Promise<void> {
  await apiJson("/api/v1/auth/logout", { method: "POST" });
}

// ────────────────────────────────────────────────────────
// fetchCurrentUser
// Feature: auth
// Endpoint: GET /auth/me
// Use: load the logged-in user profile on app boot.
// ────────────────────────────────────────────────────────

export async function fetchCurrentUser(): Promise<UserProfile> {
  return apiJson<UserProfile>("/api/v1/auth/me");
}
