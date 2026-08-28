/**
 * Shared test mocks for fetch, SSE, and auth context.
 */

import type { ReactNode } from "react";

// ────────────────────────────────────────────────────────────
// jsonResponse
// Feature: test helpers
// Use: build a mock fetch Response with JSON body.
// ────────────────────────────────────────────────────────────

export function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

// ────────────────────────────────────────────────────────────
// sseResponse
// Feature: test helpers
// Use: build a mock SSE stream for POST /chat/stream integration tests.
// ────────────────────────────────────────────────────────────

export function sseResponse(
  events: Array<{ event: string; data: Record<string, unknown> }>,
): Response {
  const payload = events
    .map((item) => `event: ${item.event}\ndata: ${JSON.stringify(item.data)}\n\n`)
    .join("");
  const bytes = new TextEncoder().encode(payload);
  let consumed = false;

  // whatwg-fetch Response does not expose ReadableStream bodies in jsdom —
  // return a minimal Response shape that readSse can consume in tests.
  const reader = {
    read: async (): Promise<ReadableStreamReadResult<Uint8Array>> => {
      if (consumed) return { done: true, value: undefined };
      consumed = true;
      return { done: false, value: bytes };
    },
  };

  return {
    status: 200,
    ok: true,
    body: { getReader: () => reader },
  } as unknown as Response;
}

// ────────────────────────────────────────────────────────────
// mockAuthContext
// Feature: test helpers
// Use: fake auth values for hook and form component tests.
// ────────────────────────────────────────────────────────────

export const mockAuthContext = {
  authReady: true,
  isAuthenticated: true,
  userEmail: "test@example.com",
  login: jest.fn().mockResolvedValue(undefined),
  register: jest.fn().mockResolvedValue(undefined),
  logout: jest.fn().mockResolvedValue(undefined),
  error: null as string | null,
  clearError: jest.fn(),
};

// ────────────────────────────────────────────────────────────
// noopChildren
// Feature: test helpers
// Use: placeholder child for provider wrapper tests.
// ────────────────────────────────────────────────────────────

export function noopChildren(): ReactNode {
  return null;
}
