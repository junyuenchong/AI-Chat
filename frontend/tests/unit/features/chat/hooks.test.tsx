/**
 * Unit tests for features/chat/hooks.ts — useChat.
 */

import { act, renderHook, waitFor } from "@testing-library/react";

import { useChat } from "@/features/chat/hooks";

jest.mock("@/features/chat/api", () => ({
  streamChat: jest.fn((_body, onEvent) => {
    onEvent("meta", { conversation_id: "conv-1" });
    onEvent("token", { content: "Hi" });
    onEvent("done", { conversation_id: "conv-1", content: "Hi" });
    return Promise.resolve();
  }),
  formatStreamError: jest.fn((_data, fallback) => fallback),
}));

// ────────────────────────────────────────────────────────────
// useChat
// Feature: chat
// Endpoint: POST /chat/stream
// Use: accumulate bubbles and streaming state from SSE events.
// ────────────────────────────────────────────────────────────

describe("useChat", () => {
  it("appends user and assistant messages after send", async () => {
    const onConversationId = jest.fn();
    const onTitleFromMessage = jest.fn();
    const onAfterSend = jest.fn().mockResolvedValue(undefined);

    const { result } = renderHook(() =>
      useChat({
        conversationId: null,
        onConversationId,
        onTitleFromMessage,
        onAfterSend,
      }),
    );

    act(() => {
      result.current.setInput("Hello");
    });

    await act(async () => {
      await result.current.sendMessage();
    });

    await waitFor(() => {
      expect(result.current.streaming).toBe(false);
    });

    const roles = result.current.bubbles.map((b) => b.role);
    expect(roles).toContain("user");
    expect(roles).toContain("assistant");
    expect(onConversationId).toHaveBeenCalledWith("conv-1");
    expect(onAfterSend).toHaveBeenCalled();
  });

  it("does not send when input is blank", async () => {
    const { result } = renderHook(() =>
      useChat({
        conversationId: null,
        onConversationId: jest.fn(),
        onTitleFromMessage: jest.fn(),
        onAfterSend: jest.fn(),
      }),
    );

    await act(async () => {
      await result.current.sendMessage();
    });

    expect(result.current.bubbles).toHaveLength(1); // Only the initial assistant bubble.
  });
});
