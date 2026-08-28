"use client";

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
      const messages = await conv.openConversation(id);
      if (messages && messageLoader) messageLoader(messages);
    },
    [conv, messageLoader],
  );

  const registerResetHandler = useCallback((reset: ResetMessages) => {
    resetRef.current = reset;
  }, []);

  const startNewConversation = useCallback(() => {
    conv.startNewChat();
    resetRef.current?.("New chat. Ask about LangChain, RAG, or your uploaded knowledge.");
  }, [conv]);

  const value = useMemo(
    () => ({
      ...conv,
      selectConversation,
      startNewConversation,
      registerMessageLoader,
      registerResetHandler,
    }),
    [conv, selectConversation, startNewConversation, registerMessageLoader, registerResetHandler],
  );

  return <ConversationContext.Provider value={value}>{children}</ConversationContext.Provider>;
}

// ────────────────────────────────────────────────────────
// useConversationContext
// Feature: conversations
// Use: access sidebar thread state and selection handlers.
// ────────────────────────────────────────────────────────

export function useConversationContext(): ConversationContextValue {
  const ctx = useContext(ConversationContext);
  if (!ctx) throw new Error("useConversationContext must be used within ConversationProvider");
  return ctx;
}
