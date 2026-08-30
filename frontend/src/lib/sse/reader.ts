// ────────────────────────────────────────────────────────
// parseSsePart
// Feature: shared
// Use: parse one SSE block (event + data lines) from the stream buffer.
// ────────────────────────────────────────────────────────

function parseSsePart(
  part: string,
): { event: string; data: Record<string, unknown> } | null {
  const trimmed = part.trim();
  if (!trimmed) return null;
  let event = "message";
  const dataLines: string[] = [];
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
// Feature: shared
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
// Feature: shared
// Use: read POST /chat/stream body and emit meta, token, done, error events.
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
    buffer += decoder.decode(value, { stream: true }).replace(/\r\n/g, "\n");
    const parts = buffer.split("\n\n");
    buffer = parts.pop() ?? ""; // Keep incomplete chunk for the next read.
    dispatchSseParts(parts, onEvent);
  }
  buffer += decoder.decode().replace(/\r\n/g, "\n");
  if (buffer.trim()) {
    dispatchSseParts([buffer], onEvent);
  }
}
