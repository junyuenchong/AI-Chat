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
    registerMessageLoader(loadMessages);
    registerResetHandler((welcome) => resetBubbles(welcome));
  }, [registerMessageLoader, registerResetHandler, loadMessages, resetBubbles]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const error = convError || chatError;

  return (
    <>
      <header className="flex items-center justify-between border-b border-line px-5 py-3.5">
        <div>
          <strong className="text-sm">{activeTitle}</strong>
          <br />
          <span className="text-xs text-muted">
            Next.js · FastAPI · LangChain · RAG · SSE
          </span>
        </div>
        <a
          href={`${API_BASE}/docs`}
          target="_blank"
          rel="noreferrer"
          className="text-[13px] text-accent no-underline"
        >
          OpenAPI
        </a>
      </header>
      <MessageList bubbles={bubbles} streaming={streaming} messagesRef={messagesRef} />
      {error ? <div className="px-5 pb-2 text-xs text-warn">{error}</div> : null}
      <div className="px-5 pb-2 text-xs text-muted">
        Session cookie + SSE via same-origin proxy.
      </div>
      <ChatInput
        value={input}
        streaming={streaming}
        onChange={setInput}
        onSubmit={sendMessage}
      />
    </>
  );
}
