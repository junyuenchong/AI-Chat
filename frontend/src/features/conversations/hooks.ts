"use client";

import { useCallback, useState } from "react";

import { getConversation, listConversations } from "./api";
import type { Conversation } from "./types";

// ────────────────────────────────────────────────────────
// useConversations
// Feature: conversations
// Endpoint: GET /conversations, GET /conversations/{id}
// Use: sidebar thread list, open thread, and refresh after chat.
// ────────────────────────────────────────────────────────

export function useConversations() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [activeTitle, setActiveTitle] = useState("New conversation");
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const rows = await listConversations();
      setConversations(rows);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load conversations.");
    }
  }, []);

  const openConversation = useCallback(
    async (id: string) => {
      setError(null);
      try {
        const data = await getConversation(id);
        setActiveId(id);
        setActiveTitle(data.title);
        await refresh();
        return data.messages.map((msg) => ({
          role: msg.role as "user" | "assistant",
          content: msg.content,
        }));
      } catch (err) {
        setError(err instanceof Error ? err.message : "Could not open conversation.");
        return null;
      }
    },
    [refresh],
  );

  const startNewChat = useCallback(() => {
    setActiveId(null);
    setActiveTitle("New conversation");
  }, []);

  return {
    conversations,
    activeId,
    activeTitle,
    setActiveTitle,
    setActiveId,
    error,
    refresh,
    openConversation,
    startNewChat,
  };
}
