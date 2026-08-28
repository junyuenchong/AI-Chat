/**
 * Unit tests for lib/sse/reader.ts — SSE stream parsing.
 */

import { readSse } from "@/lib/sse/reader";

import { sseResponse } from "../../../helpers/mocks";

// ────────────────────────────────────────────────────────────
// readSse
// Feature: shared
// Endpoint: POST /chat/stream
// Use: parse meta, token, and done events from the response body.
// ────────────────────────────────────────────────────────────

describe("readSse", () => {
  it("emits parsed events in order", async () => {
    const events: Array<[string, Record<string, unknown>]> = [];
    const res = sseResponse([
      { event: "meta", data: { conversation_id: "c-1", route: "direct" } },
      { event: "token", data: { content: "Hi" } },
      { event: "done", data: { content: "Hi", conversation_id: "c-1" } },
    ]);

    await readSse(res, (name, data) => {
      events.push([name, data]);
    });

    expect(events.map(([name]) => name)).toEqual(["meta", "token", "done"]);
    expect(events[1][1].content).toBe("Hi");
  });

  it("throws when response has no body", async () => {
    const res = new Response(null);
    await expect(readSse(res, jest.fn())).rejects.toThrow("No response body");
  });
});
