import { authHeaders, formatApiError, readError, streamUrl } from "@/lib/api/client";
import { readSse } from "@/lib/sse/reader";

import type { StreamChatBody } from "./types";

// ────────────────────────────────────────────────────────
// streamChat
// Feature: chat
// Endpoint: POST /chat/stream
// Use: send a message and receive SSE meta, token, and done events.
// ────────────────────────────────────────────────────────

export async function streamChat(
  body: StreamChatBody,
  onEvent: (event: string, data: Record<string, unknown>) => void,
): Promise<void> {
  const res = await fetch(streamUrl("/api/v1/chat/stream"), {
    method: "POST",
    credentials: "include",
    headers: authHeaders(),
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const text = await readError(res, "Chat request failed.");
    onEvent("error", { message: text, code: "HTTP_ERROR" });
    return;
  }
  await readSse(res, onEvent);
}

// ────────────────────────────────────────────────────────
// formatStreamError
// Feature: chat
// Use: normalize SSE error events into user-visible text.
// ────────────────────────────────────────────────────────

export function formatStreamError(data: Record<string, unknown>, fallback: string): string {
  return formatApiError({ error: data as { message?: string; fields?: unknown[] } }, fallback);
}
