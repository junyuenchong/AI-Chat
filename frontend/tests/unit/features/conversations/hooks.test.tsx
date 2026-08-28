/**
 * Unit tests for features/conversations/hooks.ts — useConversations.
 */

import { act, renderHook, waitFor } from "@testing-library/react";

import { useConversations } from "@/features/conversations/hooks";

jest.mock("@/features/conversations/api", () => ({
  listConversations: jest.fn().mockResolvedValue([{ id: "c1", title: "First chat", updated_at: "2026-01-01" }]),
  getConversation: jest.fn().mockResolvedValue({
    id: "c1",
    title: "First chat",
    messages: [{ role: "user", content: "Hi" }],
  }),
}));

// ────────────────────────────────────────────────────────────
// useConversations
// Feature: conversations
// Endpoint: GET /conversations, GET /conversations/{id}
// Use: load sidebar threads and open a conversation by id.
// ────────────────────────────────────────────────────────────

describe("useConversations", () => {
  it("opens conversation and returns message bubbles", async () => {
    const { result } = renderHook(() => useConversations());

    let messages: Array<{ role: string; content: string }> | null = null;
    await act(async () => {
      messages = await result.current.openConversation("c1");
    });

    expect(messages).toEqual([{ role: "user", content: "Hi" }]);
    expect(result.current.activeId).toBe("c1");
    expect(result.current.activeTitle).toBe("First chat");
  });

  it("resets state when starting a new chat", async () => {
    const { result } = renderHook(() => useConversations());

    await act(async () => {
      await result.current.openConversation("c1");
    });

    act(() => {
      result.current.startNewChat();
    });

    expect(result.current.activeId).toBeNull();
    expect(result.current.activeTitle).toBe("New conversation");
  });

  it("refreshes conversation list from API", async () => {
    const { result } = renderHook(() => useConversations());

    await act(async () => {
      await result.current.refresh();
    });

    await waitFor(() => {
      expect(result.current.conversations).toHaveLength(1);
    });
  });
});
