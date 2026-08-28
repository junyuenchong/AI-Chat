// ────────────────────────────────────────────────────────
// scrollToBottom
// Feature: chat
// Use: keep the message list pinned to the latest bubble while streaming.
// ────────────────────────────────────────────────────────

export function scrollToBottom(container: HTMLElement | null) {
  if (container) container.scrollTop = container.scrollHeight;
}

// ────────────────────────────────────────────────────────
// welcomeMessage
// Feature: chat
// Use: default assistant text for a new or signed-out chat pane.
// ────────────────────────────────────────────────────────

export function welcomeMessage(signedIn: boolean): string {
  if (!signedIn) return "Sign in to start chatting.";
  return "New chat. Ask about LangChain, RAG, or your uploaded knowledge.";
}
