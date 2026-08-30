/**
 * Unit tests for lib/api/client.ts — URL building and error formatting.
 */

import {
  apiJson,
  apiUrl,
  authHeaders,
  formatApiError,
  readError,
  streamUrl,
} from "@/lib/api/client";

import { jsonResponse } from "../../../helpers/mocks";

// ────────────────────────────────────────────────────────────
// apiUrl / streamUrl
// Feature: shared
// Endpoint: all /api/v1/* routes
// Use: browser uses same-origin path; server-side uses API_BASE prefix.
// ────────────────────────────────────────────────────────────

describe("apiUrl", () => {
  it("returns path only in browser context", () => {
    expect(apiUrl("/api/v1/health")).toBe("/api/v1/health");
  });

  it("streamUrl delegates to apiUrl", () => {
    expect(streamUrl("/api/v1/chat/stream")).toBe("/api/v1/chat/stream");
  });
});

// ────────────────────────────────────────────────────────────
// formatApiError
// Feature: shared
// Use: flatten backend error envelope for UI display.
// ────────────────────────────────────────────────────────────

describe("formatApiError", () => {
  it("returns message and field errors", () => {
    const text = formatApiError(
      {
        error: {
          message: "Invalid",
          fields: [{ field: "email", message: "Required" }],
        },
      },
      "fallback",
    );
    expect(text).toContain("Invalid");
    expect(text).toContain("email");
  });

  it("falls back when payload has no error object", () => {
    expect(formatApiError({}, "fallback")).toBe("fallback");
  });
});

// ────────────────────────────────────────────────────────────
// authHeaders
// Feature: shared
// Use: optional Bearer token for API clients.
// ────────────────────────────────────────────────────────────

describe("authHeaders", () => {
  it("includes Authorization when token is provided", () => {
    const headers = authHeaders("jwt-token");
    expect(headers.Authorization).toBe("Bearer jwt-token");
  });
});

// ────────────────────────────────────────────────────────────
// apiJson
// Feature: shared
// Endpoint: all JSON API routes
// Use: fetch with credentials and throw on non-OK status.
// ────────────────────────────────────────────────────────────

describe("apiJson", () => {
  beforeEach(() => {
    global.fetch = jest.fn();
  });

  it("returns parsed JSON on success", async () => {
    (global.fetch as jest.Mock).mockResolvedValue(jsonResponse({ ok: true }));
    const data = await apiJson<{ ok: boolean }>("/api/v1/health");
    expect(data.ok).toBe(true);
    expect(global.fetch).toHaveBeenCalledWith(
      "/api/v1/health",
      expect.objectContaining({ credentials: "include" }),
    );
  });

  it("throws readable error on failure", async () => {
    (global.fetch as jest.Mock).mockResolvedValue(
      jsonResponse({ error: { message: "Unauthorized" } }, 401),
    );
    await expect(apiJson("/api/v1/conversations")).rejects.toThrow("Unauthorized");
  });
});

// ────────────────────────────────────────────────────────────
// readError
// Feature: shared
// Use: parse failed Response body into error text.
// ────────────────────────────────────────────────────────────

describe("readError", () => {
  it("includes status when body is not JSON", async () => {
    const res = new Response("not json", { status: 500 });
    const text = await readError(res, "Server error");
    expect(text).toBe("Server error (500)");
  });
});
