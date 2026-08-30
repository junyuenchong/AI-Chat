/**
 * SSE stream reader — parse Server-Sent Events from POST /chat/stream.
 *
 * Request path:
 *   features/chat/api.ts
 *     → lib/sse/reader.ts  (this file)
 */

// ────────────────────────────────────────────────────────
// parseSsePart
// Path: lib/sse/reader.ts
// Use: parse one SSE block (event + data lines) from the stream buffer.
// ────────────────────────────────────────────────────────
function parseSsePart(
  part: string,
): { event: string; data: Record<string, unknown> } | null {
  const trimmed = part.trim();
  if (!trimmed) return null;
  let event = "message";
  const dataLines: string[] = [];
  // Step 1 — split lines and collect event name + data payload.
  for (const line of trimmed.split("\n")) {
    if (line.startsWith("event:")) event = line.slice(6).trim();
    if (line.startsWith("data:")) dataLines.push(line.slice(5).trim());
  }
  if (!dataLines.length) return null;
  const raw = dataLines.join("\n");
  try {
    return { event, data: JSON.parse(raw) as Record<string, unknown> };
  } catch {
    return { event, data: { content: raw } }; // Non-JSON payloads still surface as content.
  }
}

// ────────────────────────────────────────────────────────
// dispatchSseParts
// Path: lib/sse/reader.ts
// Use: fan out parsed SSE parts to the chat event handler.
// ────────────────────────────────────────────────────────
function dispatchSseParts(
  parts: string[],
  onEvent: (event: string, data: Record<string, unknown>) => void,
) {
  for (const part of parts) {
    const parsed = parseSsePart(part);
    if (parsed) onEvent(parsed.event, parsed.data);
  }
}

// ────────────────────────────────────────────────────────
// readSse
// Path: lib/sse/reader.ts
// Endpoint: POST /chat/stream
// Use: read response body and emit meta, token, done, error events.
// ────────────────────────────────────────────────────────
export async function readSse(
  response: Response,
  onEvent: (event: string, data: Record<string, unknown>) => void,
): Promise<void> {
  const reader = response.body?.getReader();
  if (!reader) throw new Error("No response body");
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    // Step 1 — append chunk and split on blank line (SSE frame boundary).
    buffer += decoder.decode(value, { stream: true }).replace(/\r\n/g, "\n");
    const parts = buffer.split("\n\n");
    buffer = parts.pop() ?? ""; // Keep incomplete chunk for the next read.
    dispatchSseParts(parts, onEvent);
  }
  // Step 2 — flush any trailing data after the stream closes.
  buffer += decoder.decode().replace(/\r\n/g, "\n");
  if (buffer.trim()) {
    dispatchSseParts([buffer], onEvent);
  }
}
