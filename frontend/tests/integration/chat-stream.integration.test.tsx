/**
 * Integration test — chat UI → streamChat API → bubble state.
 */

import { act, renderHook, waitFor } from "@testing-library/react";

import { streamChat } from "@/features/chat/api";
import { useChat } from "@/features/chat/hooks";

import { sseResponse } from "../helpers/mocks";

jest.mock("@/features/chat/api", () => ({
  ...jest.requireActual("@/features/chat/api"),
  streamChat: jest.fn(),
}));

const mockedStreamChat = streamChat as jest.MockedFunction<typeof streamChat>;

// ────────────────────────────────────────────────────────────
// chat stream integration
// Feature: chat
// Endpoint: POST /chat/stream
// Use: verify hook updates state when API emits SSE token events.
// ────────────────────────────────────────────────────────────

describe("chat stream integration", () => {
  beforeEach(() => {
    mockedStreamChat.mockImplementation(async (_body, onEvent) => {
      onEvent("meta", { conversation_id: "conv-99", route: "direct" });
      onEvent("token", { content: "Hello " });
      onEvent("token", { content: "world" });
      onEvent("done", { conversation_id: "conv-99", content: "Hello world" });
    });
  });

  it("accumulates streamed tokens into assistant bubble", async () => {
    const onConversationId = jest.fn();
    const { result } = renderHook(() =>
      useChat({
        conversationId: null,
        onConversationId,
        onTitleFromMessage: jest.fn(),
        onAfterSend: jest.fn().mockResolvedValue(undefined),
      }),
    );

    act(() => {
      result.current.setInput("Say hi");
    });

    // Wait for useCallback to see the updated input before send.
    await waitFor(() => {
      expect(result.current.input).toBe("Say hi");
    });

    await act(async () => {
      await result.current.sendMessage();
    });

    await waitFor(() => {
      // Use the last assistant bubble — the first one is the welcome message.
      const assistant = [...result.current.bubbles]
        .reverse()
        .find((b) => b.role === "assistant");
      expect(assistant?.content).toContain("Hello world");
    });

    expect(onConversationId).toHaveBeenCalledWith("conv-99");
    expect(mockedStreamChat).toHaveBeenCalledWith(
      expect.objectContaining({ message: "Say hi" }),
      expect.any(Function),
    );
  });

  it("readSse parses mock response end-to-end", async () => {
    const { readSse } = await import("@/lib/sse/reader");
    const res = sseResponse([
      { event: "token", data: { content: "A" } },
      { event: "done", data: { content: "A" } },
    ]);
    const names: string[] = [];
    await readSse(res, (name) => names.push(name));
    expect(names).toEqual(["token", "done"]);
  });
});
