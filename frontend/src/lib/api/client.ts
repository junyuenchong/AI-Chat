import type { ApiErrorBody } from "@/lib/types/common";

export const API_BASE =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") || "http://localhost:8000";

// ────────────────────────────────────────────────────────
// apiUrl
// Feature: shared
// Use: build request URLs — browser uses same-origin /api/v1 proxy.
// ────────────────────────────────────────────────────────

export function apiUrl(path: string): string {
  const prefix = typeof window === "undefined" ? API_BASE : "";
  return `${prefix}${path}`;
}

// ────────────────────────────────────────────────────────
// streamUrl
// Feature: shared
// Use: SSE requests through the same proxy so session cookies are sent.
// ────────────────────────────────────────────────────────

export function streamUrl(path: string): string {
  return apiUrl(path);
}

// ────────────────────────────────────────────────────────
// formatApiError
// Feature: shared
// Use: turn backend error JSON into a readable string for the UI.
// ────────────────────────────────────────────────────────

export function formatApiError(payload: ApiErrorBody | unknown, fallback: string): string {
  const body = payload as ApiErrorBody;
  const err = body?.error ?? (payload as ApiErrorBody["error"]);
  if (!err) return fallback;
  const message =
    typeof err.message === "string" && err.message.trim() ? err.message.trim() : fallback;
  const fields = Array.isArray(err.fields) ? err.fields : [];
  const fieldText = fields
    .map((item) => `${item.field ? `${item.field}: ` : ""}${item.message || ""}`)
    .filter(Boolean)
    .join(" ");
  return [message, fieldText].filter(Boolean).join(" ") || fallback;
}

// ────────────────────────────────────────────────────────
// readError
// Feature: shared
// Use: parse a failed fetch Response into an error message.
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
// Feature: shared
// Use: JSON headers — browsers rely on HttpOnly cookie; Bearer is optional.
// ────────────────────────────────────────────────────────

export function authHeaders(token?: string, extra: Record<string, string> = {}) {
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...extra,
  };
}

// ────────────────────────────────────────────────────────
// apiJson
// Feature: shared
// Use: generic JSON fetch with credentials and unified error handling.
// ────────────────────────────────────────────────────────

export async function apiJson<T>(
  path: string,
  init: RequestInit & { token?: string } = {},
): Promise<T> {
  const { token, headers, ...rest } = init;
  const res = await fetch(apiUrl(path), {
    ...rest,
    credentials: "include", // Session cookie forwarded to FastAPI via proxy.
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(headers || {}),
    },
  });
  if (!res.ok) {
    throw new Error(await readError(res, "Request failed"));
  }
  if (res.status === 204) {
    return undefined as T;
  }
  return (await res.json()) as T;
}
