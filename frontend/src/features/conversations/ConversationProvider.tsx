"use client";

/**
 * Conversation context — bridges sidebar selection and chat message loader.
 *
 * Request path:
 *   DashboardLayout → ConversationProvider
 *     → ChatPage (registers loadMessages / resetBubbles)
 */

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";

import type { ChatBubble } from "@/features/chat/types";

import { useConversations } from "./hooks";

type MessageLoader = (messages: ChatBubble[]) => void;
type ResetMessages = (welcome: string) => void;

type ConversationContextValue = ReturnType<typeof useConversations> & {
  selectConversation: (id: string) => Promise<void>;
  startNewConversation: () => void;
  registerMessageLoader: (loader: MessageLoader) => void;
  registerResetHandler: (reset: ResetMessages) => void;
};

const ConversationContext = createContext<ConversationContextValue | null>(null);

// ────────────────────────────────────────────────────────
// ConversationProvider
// Feature: conversations
// Use: share thread list between sidebar and chat page message loader.
// ────────────────────────────────────────────────────────

export function ConversationProvider({ children }: { children: ReactNode }) {
  const conv = useConversations();
  const [messageLoader, setMessageLoader] = useState<MessageLoader | null>(null);
  const resetRef = useRef<ResetMessages | null>(null);

  const registerMessageLoader = useCallback((loader: MessageLoader) => {
    setMessageLoader(() => loader);
  }, []);

  const selectConversation = useCallback(
    async (id: string) => {
      // Step 1 — fetch messages from API.
      const messages = await conv.openConversation(id);
      // Step 2 — push them into the chat pane via registered loader.
      if (messages && messageLoader) messageLoader(messages);
    },
    [conv, messageLoader],
  );

  const registerResetHandler = useCallback((reset: ResetMessages) => {
    resetRef.current = reset;
  }, []);

  const startNewConversation = useCallback(() => {
    conv.startNewChat();
    // Clear chat pane and show welcome text for a new thread.
    resetRef.current?.(
      "New chat. Send a message to start streaming.",
    );
  }, [conv]);

  const value = useMemo(
    () => ({
      ...conv,
      selectConversation,
      startNewConversation,
      registerMessageLoader,
      registerResetHandler,
    }),
    [
      conv,
      selectConversation,
      startNewConversation,
      registerMessageLoader,
      registerResetHandler,
    ],
  );

  return (
    <ConversationContext.Provider value={value}>
      {children}
    </ConversationContext.Provider>
  );
}

// ────────────────────────────────────────────────────────
// useConversationContext
// Feature: conversations
// Use: access sidebar thread state and selection handlers.
// ────────────────────────────────────────────────────────

export function useConversationContext(): ConversationContextValue {
  const ctx = useContext(ConversationContext);
  if (!ctx)
    throw new Error("useConversationContext must be used within ConversationProvider");
  return ctx;
}
