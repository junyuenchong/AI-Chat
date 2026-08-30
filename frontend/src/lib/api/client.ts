/**
 * Shared HTTP client for the FastAPI backend.
 *
 * Request path:
 *   features/auth|chat|conversations/api.ts
 *     -> lib/api/client.ts  (this file)
 *     -> /api/v1/[...path]/route.ts (browser) or FastAPI directly (SSR)
 */

import type { ApiErrorBody } from "@/lib/types/common";
import { getAccessToken } from "@/lib/auth/token";

export const API_BASE =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") || "http://localhost:8000";

// ────────────────────────────────────────────────────────
// apiUrl
// Path: lib/api/client.ts
// Use: build the fetch URL — same-origin proxy in browser, direct on server.
// ────────────────────────────────────────────────────────
export function apiUrl(path: string): string {
  // Step 1 — browser uses Next.js proxy at /api/v1/* (no host prefix).
  const prefix = typeof window === "undefined" ? API_BASE : "";
  return `${prefix}${path}`;
}

// ────────────────────────────────────────────────────────
// streamUrl
// Path: lib/api/client.ts
// Endpoint: POST /chat/stream
// Use: same as apiUrl — SSE chat goes through the same proxy.
// ────────────────────────────────────────────────────────
export function streamUrl(path: string): string {
  return apiUrl(path);
}

// ────────────────────────────────────────────────────────
// formatApiError
// Path: lib/api/client.ts
// Use: turn FastAPI error JSON into one readable string for the UI.
// ────────────────────────────────────────────────────────
export function formatApiError(
  payload: ApiErrorBody | unknown,
  fallback: string,
): string {
  const body = payload as ApiErrorBody;
  const err = body?.error ?? (payload as ApiErrorBody["error"]);
  if (!err) return fallback;
  // Step 1 — main message from the API envelope.
  const message =
    typeof err.message === "string" && err.message.trim()
      ? err.message.trim()
      : fallback;
  // Step 2 — append field-level validation errors when present.
  const fields = Array.isArray(err.fields) ? err.fields : [];
  const fieldText = fields
    .map((item) => `${item.field ? `${item.field}: ` : ""}${item.message || ""}`)
    .filter(Boolean)
    .join(" ");
  return [message, fieldText].filter(Boolean).join(" ") || fallback;
}

// ────────────────────────────────────────────────────────
// readError
// Path: lib/api/client.ts
// Use: parse a failed fetch Response body into an error message.
// ────────────────────────────────────────────────────────
export async function readError(res: Response, fallback: string): Promise<string> {
  try {
    const payload = (await res.json()) as ApiErrorBody;
    return formatApiError(payload, fallback);
  } catch {
    return `${fallback} (${res.status})`;
  }
}

// ────────────────────────────────────────────────────────
// authHeaders
// Path: lib/api/client.ts
// Use: attach JSON content-type and JWT Bearer token to requests.
// ────────────────────────────────────────────────────────
export function authHeaders(token?: string, extra: Record<string, string> = {}) {
  // Step 1 — read token from argument or sessionStorage.
  const resolved = token ?? getAccessToken() ?? undefined;
  return {
    "Content-Type": "application/json",
    ...(resolved ? { Authorization: `Bearer ${resolved}` } : {}),
    ...extra,
  };
}

// ────────────────────────────────────────────────────────
// apiJson
// Path: lib/api/client.ts
// Use: typed JSON fetch wrapper — throws on non-OK status.
// ────────────────────────────────────────────────────────
export async function apiJson<T>(
  path: string,
  init: RequestInit & { token?: string } = {},
): Promise<T> {
  const { token, headers, ...rest } = init;
  // Step 1 — call the API with auth headers.
  const res = await fetch(apiUrl(path), {
    ...rest,
    headers: {
      ...authHeaders(token),
      ...(headers || {}),
    },
  });
  // Step 2 — surface API errors as thrown exceptions.
  if (!res.ok) {
    throw new Error(await readError(res, "Request failed"));
  }
  if (res.status === 204) {
    return undefined as T;
  }
  return (await res.json()) as T;
}
