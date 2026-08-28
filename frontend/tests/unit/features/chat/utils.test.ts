/**
 * Unit tests for features/chat/utils.ts
 */

import { scrollToBottom, welcomeMessage } from "@/features/chat/utils";

// ────────────────────────────────────────────────────────────
// scrollToBottom
// Feature: chat
// Use: pin message list to the latest bubble.
// ────────────────────────────────────────────────────────────

describe("scrollToBottom", () => {
  it("sets scrollTop to scrollHeight", () => {
    const el = document.createElement("div");
    Object.defineProperty(el, "scrollHeight", { value: 400 });
    scrollToBottom(el);
    expect(el.scrollTop).toBe(400);
  });

  it("does nothing when container is null", () => {
    expect(() => scrollToBottom(null)).not.toThrow();
  });
});

// ────────────────────────────────────────────────────────────
// welcomeMessage
// Feature: chat
// Use: default assistant text for new or signed-out sessions.
// ────────────────────────────────────────────────────────────

describe("welcomeMessage", () => {
  it("prompts sign-in when logged out", () => {
    expect(welcomeMessage(false)).toContain("Sign in");
  });

  it("shows new chat hint when logged in", () => {
    expect(welcomeMessage(true)).toContain("New chat");
  });
});
