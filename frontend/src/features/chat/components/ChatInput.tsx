"use client";

import { FormEvent } from "react";

import { Button } from "@/components/ui/Button";

type ChatInputProps = {
  value: string;
  streaming: boolean;
  onChange: (value: string) => void;
  onSubmit: (event: FormEvent) => void;
};

// ────────────────────────────────────────────────────────
// ChatInput
// Feature: chat
// Endpoint: POST /chat/stream
// Use: message composer — Enter sends, Shift+Enter adds a new line.
// ────────────────────────────────────────────────────────

export function ChatInput({ value, streaming, onChange, onSubmit }: ChatInputProps) {
  return (
    <form
      className="grid shrink-0 grid-cols-1 gap-2.5 border-t border-line px-4 pb-4 pt-3 sm:grid-cols-[1fr_auto] sm:px-5 sm:pb-5 sm:pt-4"
      onSubmit={onSubmit}
    >
      <textarea
        className="min-h-[52px] max-h-40 w-full resize-y rounded-xl border border-line bg-panel px-3 py-3 text-base text-text placeholder:text-muted focus:outline-none focus:ring-2 focus:ring-accent/40 sm:text-sm"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={streaming ? "Waiting for reply..." : "Send a message..."}
        onKeyDown={(e) => {
          if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            e.currentTarget.form?.requestSubmit();
          }
        }}
      />
      <Button type="submit" className="w-full sm:w-auto" disabled={streaming || !value.trim()}>
        {streaming ? "Sending..." : "Send"}
      </Button>
    </form>
  );
}
