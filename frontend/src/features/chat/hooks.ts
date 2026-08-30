"use client";

import { FormEvent, useCallback, useEffect, useRef, useState } from "react";

import { formatStreamError, streamChat } from "./api";
import type { ChatBubble } from "./types";
import { scrollToBottom } from "./utils";

type UseChatOptions = {
  conversationId: string | null;
  onConversationId: (id: string) => void;
  onTitleFromMessage: (title: string) => void;
  onAfterSend: () => Promise<void>;
};

// ────────────────────────────────────────────────────────
// useChat
// Feature: chat
// Endpoint: POST /chat/stream
// Use: manage message bubbles, streaming state, and send handler.
// ────────────────────────────────────────────────────────

export function useChat({
  conversationId,
  onConversationId,
  onTitleFromMessage,
  onAfterSend,
}: UseChatOptions) {
  const [bubbles, setBubbles] = useState<ChatBubble[]>([
    { role: "assistant", content: "Stack is up. Send a message to start." },
  ]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollToBottom(messagesRef.current);
  }, [bubbles]);

  const resetBubbles = useCallback((content: string) => {
    setBubbles([{ role: "assistant", content }]);
  }, []);

  const loadMessages = useCallback((messages: ChatBubble[]) => {
    setBubbles(
      messages.length ? messages : [{ role: "assistant", content: "No messages yet." }],
    );
  }, []);

  const sendMessage = useCallback(
    async (event?: FormEvent) => {
      event?.preventDefault();
      if (streaming) return;
      const message = input.trim();
      if (!message) return;
      setInput("");
      setError(null);
      setBubbles((prev) => [
        ...prev,
        { role: "user", content: message },
        { role: "assistant", content: "" },
      ]);
      setStreaming(true);
      try {
        const body: { message: string; use_rag: boolean; conversation_id?: string } = {
          message,
          use_rag: true,
        };
        if (conversationId) body.conversation_id = conversationId;

        await streamChat(body, (eventName, data) => {
          if (eventName === "meta" && typeof data.conversation_id === "string") {
            onConversationId(data.conversation_id);
          }
          const tokenText =
            (eventName === "token" || eventName === "message") &&
            typeof data.content === "string"
              ? data.content
              : null;
          if (tokenText) {
            setBubbles((prev) => {
              const next = [...prev];
              const last = next[next.length - 1];
              next[next.length - 1] = {
                role: "assistant",
                content: (last?.content || "") + tokenText,
              };
              return next;
            });
          }
          if (eventName === "done") {
            if (typeof data.conversation_id === "string") {
              onConversationId(data.conversation_id);
              onTitleFromMessage(message.slice(0, 80));
            }
            if (typeof data.content === "string" && data.content) {
              setBubbles((prev) => {
                const next = [...prev];
                const last = next[next.length - 1];
                if (last?.role !== "assistant") return next;
                next[next.length - 1] = {
                  role: "assistant",
                  content: last.content || (data.content as string),
                };
                return next;
              });
            }
          }
          if (eventName === "error") {
            setBubbles((prev) => {
              const next = [...prev];
              next[next.length - 1] = {
                role: "assistant",
                content: formatStreamError(data, "Stream error"),
              };
              return next;
            });
          }
        });
        await onAfterSend();
      } catch (err) {
        setBubbles((prev) => {
          const next = [...prev];
          next[next.length - 1] = {
            role: "assistant",
            content: err instanceof Error ? err.message : String(err),
          };
          return next;
        });
      } finally {
        setStreaming(false);
      }
    },
    [
      streaming,
      input,
      conversationId,
      onConversationId,
      onTitleFromMessage,
      onAfterSend,
    ],
  );

  return {
    bubbles,
    input,
    setInput,
    streaming,
    error,
    setError,
    messagesRef,
    sendMessage,
    resetBubbles,
    loadMessages,
  };
}
