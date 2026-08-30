"use client";

import { useEffect } from "react";

import { ChatInput } from "@/features/chat/components/ChatInput";
import { MessageList } from "@/features/chat/components/MessageList";
import { useChat } from "@/features/chat/hooks";
import { useConversationContext } from "@/features/conversations/ConversationProvider";
import { API_BASE } from "@/lib/api/client";

// ────────────────────────────────────────────────────────
// ChatPage
// Feature: chat
// Endpoint: POST /chat/stream, GET /conversations/{id}
// Use: message list and composer for the active conversation.
// ────────────────────────────────────────────────────────

export function ChatPage() {
  const {
    activeId,
    activeTitle,
    setActiveTitle,
    setActiveId,
    error: convError,
    refresh,
    registerMessageLoader,
    registerResetHandler,
  } = useConversationContext();

  const {
    bubbles,
    input,
    setInput,
    streaming,
    error: chatError,
    messagesRef,
    sendMessage,
    resetBubbles,
    loadMessages,
  } = useChat({
    conversationId: activeId,
    onConversationId: setActiveId,
    onTitleFromMessage: setActiveTitle,
    onAfterSend: refresh,
  });

  useEffect(() => {
    // Step 1 — let ChatPage register loaders so sidebar can push history.
    registerMessageLoader(loadMessages);
    registerResetHandler((welcome) => resetBubbles(welcome));
  }, [registerMessageLoader, registerResetHandler, loadMessages, resetBubbles]);

  useEffect(() => {
    // Step 2 — load sidebar thread list on mount.
    void refresh();
  }, [refresh]);

  const error = convError || chatError;

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <header className="flex shrink-0 items-start justify-between gap-3 border-b border-line px-4 py-3 sm:px-5 sm:py-3.5">
        <div className="min-w-0">
          <strong className="block truncate text-sm">{activeTitle}</strong>
          <span className="hidden text-xs text-muted sm:inline">
            Next.js · FastAPI · LangChain · SSE
          </span>
        </div>
        <a
          href={`${API_BASE}/docs`}
          target="_blank"
          rel="noreferrer"
          className="shrink-0 text-[13px] text-accent no-underline"
        >
          OpenAPI
        </a>
      </header>
      <MessageList bubbles={bubbles} streaming={streaming} messagesRef={messagesRef} />
      {error ? <div className="px-4 pb-2 text-xs text-warn sm:px-5">{error}</div> : null}
      <div className="hidden px-4 pb-2 text-xs text-muted sm:block sm:px-5">
        JWT Bearer + SSE via same-origin proxy.
      </div>
      <ChatInput
        value={input}
        streaming={streaming}
        onChange={setInput}
        onSubmit={sendMessage}
      />
    </div>
  );
}
