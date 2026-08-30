"use client";

import type { Conversation } from "../types";
import { cn } from "@/lib/utils";

type ConversationSidebarProps = {
  conversations: Conversation[];
  activeId: string | null;
  onSelect: (id: string) => void;
};

// ────────────────────────────────────────────────────────
// ConversationSidebar
// Feature: conversations
// Endpoint: GET /conversations
// Use: show chat threads in the dashboard sidebar.
// ────────────────────────────────────────────────────────

export function ConversationSidebar({
  conversations,
  activeId,
  onSelect,
}: ConversationSidebarProps) {
  return (
    <div className="flex-1 overflow-auto px-2 pb-4">
      {conversations.map((row) => (
        <button
          key={row.id}
          type="button"
          className={cn(
            "mb-0.5 block w-full cursor-pointer rounded-[10px] border-0 px-2.5 py-2.5 text-left font-normal",
            row.id === activeId
              ? "bg-panel-2 text-text"
              : "bg-transparent text-muted hover:bg-panel-2 hover:text-text",
          )}
          onClick={() => onSelect(row.id)}
        >
          <div className="truncate">{row.title}</div>
          <small className="mt-1 block truncate text-[11px] opacity-80">
            {row.summary ? row.summary.slice(0, 80) : ""}
          </small>
        </button>
      ))}
    </div>
  );
}
