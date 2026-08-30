/**
 * Unit tests for features/chat/api.ts — streamChat wrapper.
 */

import { streamChat } from "@/features/chat/api";

import { jsonResponse, sseResponse } from "../../../helpers/mocks";

// ────────────────────────────────────────────────────────────
// streamChat
// Feature: chat
// Endpoint: POST /chat/stream
// Use: POST message and forward SSE events to the callback.
// ────────────────────────────────────────────────────────────

describe("streamChat", () => {
  beforeEach(() => {
    global.fetch = jest.fn();
  });

  it("forwards SSE events on success", async () => {
    (global.fetch as jest.Mock).mockResolvedValue(
      sseResponse([{ event: "token", data: { content: "Hello" } }]),
    );
    const events: string[] = [];
    await streamChat({ message: "hi" }, (name) => {
      events.push(name);
    });
    expect(events).toContain("token");
    expect(global.fetch).toHaveBeenCalledWith(
      "/api/v1/chat/stream",
      expect.objectContaining({
        method: "POST",
        headers: expect.objectContaining({ "Content-Type": "application/json" }),
      }),
    );
  });

  it("emits error event when HTTP status is not OK", async () => {
    (global.fetch as jest.Mock).mockResolvedValue(
      jsonResponse({ error: { message: "Unauthorized" } }, 401),
    );
    const errors: string[] = [];
    await streamChat({ message: "hi" }, (name, data) => {
      if (name === "error") errors.push(String(data.message));
    });
    expect(errors[0]).toContain("Unauthorized");
  });
});
