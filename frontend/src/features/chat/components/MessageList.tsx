"use client";

import type { RefObject } from "react";

import type { ChatBubble } from "../types";
import { MessageItem } from "./MessageItem";

type MessageListProps = {
  bubbles: ChatBubble[];
  streaming: boolean;
  messagesRef: RefObject<HTMLDivElement | null>;
};

// ────────────────────────────────────────────────────────
// MessageList
// Feature: chat
// Use: scrollable list of chat bubbles in the main pane.
// ────────────────────────────────────────────────────────

export function MessageList({ bubbles, streaming, messagesRef }: MessageListProps) {
  return (
    <div
      ref={messagesRef}
      className="flex min-h-0 flex-1 flex-col gap-3 overflow-auto p-4 sm:p-5"
    >
      {bubbles.map((bubble, index) => (
        <MessageItem
          key={`${bubble.role}-${index}`}
          bubble={bubble}
          showTyping={
            streaming &&
            index === bubbles.length - 1 &&
            bubble.role === "assistant" &&
            !bubble.content
          }
        />
      ))}
    </div>
  );
}
