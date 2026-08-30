import type { ChatBubble } from "../types";
import { cn } from "@/lib/utils";

type MessageItemProps = {
  bubble: ChatBubble;
  showTyping: boolean;
};

// ────────────────────────────────────────────────────────
// MessageItem
// Feature: chat
// Use: render one user or assistant message bubble.
// ────────────────────────────────────────────────────────

export function MessageItem({ bubble, showTyping }: MessageItemProps) {
  const isUser = bubble.role === "user";

  return (
    <div
      data-role={bubble.role}
      className={cn(
        "max-w-full whitespace-pre-wrap break-words rounded-[14px] px-3.5 py-3 leading-relaxed sm:max-w-[760px]",
        isUser ? "ml-auto bg-user" : "border border-line bg-ai",
      )}
    >
      {bubble.content ||
        (showTyping ? <span className="italic text-muted">Thinking…</span> : null)}
    </div>
  );
}
