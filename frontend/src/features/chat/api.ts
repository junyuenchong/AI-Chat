/**
 * Chat API — SSE streaming to FastAPI.
 *
 * Request path:
 *   features/chat/hooks.ts
 *     → features/chat/api.ts  (this file)
 *     → lib/sse/reader.ts
 *     → POST /api/v1/chat/stream
 */

import { authHeaders, formatApiError, readError, streamUrl } from "@/lib/api/client";
import { readSse } from "@/lib/sse/reader";

import type { StreamChatBody } from "./types";

// ────────────────────────────────────────────────────────
// streamChat
// Path: features/chat/api.ts
// Endpoint: POST /chat/stream
// Use: send a message and forward SSE events (meta, token, done, error).
// ────────────────────────────────────────────────────────
export async function streamChat(
  body: StreamChatBody,
  onEvent: (event: string, data: Record<string, unknown>) => void,
): Promise<void> {
  // Step 1 — POST with JWT Bearer header.
  const res = await fetch(streamUrl("/api/v1/chat/stream"), {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify(body),
  });
  // Step 2 — HTTP errors become an SSE-style error event.
  if (!res.ok) {
    const text = await readError(res, "Chat request failed.");
    onEvent("error", { message: text, code: "HTTP_ERROR" });
    return;
  }
  // Step 3 — parse token stream from the response body.
  await readSse(res, onEvent);
}

// ────────────────────────────────────────────────────────
// formatStreamError
// Path: features/chat/api.ts
// Use: format SSE error payload for display in the chat bubble.
// ────────────────────────────────────────────────────────
export function formatStreamError(
  data: Record<string, unknown>,
  fallback: string,
): string {
  return formatApiError(
    { error: data as { message?: string; fields?: unknown[] } },
    fallback,
  );
}
