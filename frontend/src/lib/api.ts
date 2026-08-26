import type { ApiErrorBody } from "./types";

export const API_BASE =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") || "http://localhost:8000";

/** Browser calls Next.js `/api/v1` (same origin). Avoids CORS on JSON requests. */
export function apiUrl(path: string): string {
  const prefix = typeof window === "undefined" ? API_BASE : "";
  return `${prefix}${path}`;
}

/** SSE must hit FastAPI directly — the Next.js proxy buffers event-stream chunks. */
export function streamUrl(path: string): string {
  return `${API_BASE}${path}`;
}

function parseSsePart(part: string): { event: string; data: Record<string, unknown> } | null {
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
    return { event, data: { content: raw } };
  }
}

function dispatchSseParts(parts: string[], onEvent: (event: string, data: Record<string, unknown>) => void) {
  for (const part of parts) {
    const parsed = parseSsePart(part);
    if (parsed) onEvent(parsed.event, parsed.data);
  }
}

export function formatApiError(payload: ApiErrorBody | unknown, fallback: string): string {
  const body = payload as ApiErrorBody;
  const err = body?.error ?? (payload as ApiErrorBody["error"]);
  if (!err) return fallback;
  const fields = Array.isArray(err.fields) ? err.fields : [];
  const fieldText = fields
    .map((item) => `${item.field ? `${item.field}: ` : ""}${item.message || ""}`)
    .filter(Boolean)
    .join(" ");
  return [err.message, fieldText].filter(Boolean).join(" ") || fallback;
}

export async function readError(res: Response, fallback: string): Promise<string> {
  try {
    const payload = (await res.json()) as ApiErrorBody;
    return formatApiError(payload, fallback);
  } catch {
    return `${fallback} (${res.status})`;
  }
}

export function authHeaders(token: string, extra: Record<string, string> = {}) {
  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
    ...extra,
  };
}

export async function apiJson<T>(
  path: string,
  init: RequestInit & { token?: string } = {},
): Promise<T> {
  const { token, headers, ...rest } = init;
  const res = await fetch(apiUrl(path), {
    ...rest,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(headers || {}),
    },
  });
  if (!res.ok) {
    throw new Error(await readError(res, "Request failed"));
  }
  if (res.status === 204) {
    return undefined as T;
  }
  return (await res.json()) as T;
}

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
    buffer = parts.pop() ?? "";
    dispatchSseParts(parts, onEvent);
  }
  buffer += decoder.decode().replace(/\r\n/g, "\n");
  if (buffer.trim()) {
    dispatchSseParts([buffer], onEvent);
  }
}
