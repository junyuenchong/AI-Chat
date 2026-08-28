import { apiJson } from "@/lib/api/client";

import type { Conversation, ConversationDetail } from "./types";

// ────────────────────────────────────────────────────────
// listConversations
// Feature: conversations
// Endpoint: GET /conversations
// Use: load all chat threads for the sidebar.
// ────────────────────────────────────────────────────────

export async function listConversations(): Promise<Conversation[]> {
  return apiJson<Conversation[]>("/api/v1/conversations");
}

// ────────────────────────────────────────────────────────
// getConversation
// Feature: conversations
// Endpoint: GET /conversations/{id}
// Use: open one thread with full message history.
// ────────────────────────────────────────────────────────

export async function getConversation(id: string): Promise<ConversationDetail> {
  return apiJson<ConversationDetail>(`/api/v1/conversations/${id}`);
}

// ────────────────────────────────────────────────────────
// deleteConversation
// Feature: conversations
// Endpoint: DELETE /conversations/{id}
// Use: remove a thread from the sidebar.
// ────────────────────────────────────────────────────────

export async function deleteConversation(id: string): Promise<void> {
  await apiJson(`/api/v1/conversations/${id}`, { method: "DELETE" });
}
