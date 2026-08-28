import { apiJson } from "@/lib/api/client";

import type { Document } from "./types";

// ────────────────────────────────────────────────────────
// listDocuments
// Feature: knowledge
// Endpoint: GET /documents
// Use: show uploaded documents on the knowledge page.
// ────────────────────────────────────────────────────────

export async function listDocuments(): Promise<Document[]> {
  return apiJson<Document[]>("/api/v1/documents");
}

// ────────────────────────────────────────────────────────
// uploadDocument
// Feature: knowledge
// Endpoint: POST /documents
// Use: upload text content for RAG search.
// ────────────────────────────────────────────────────────

export async function uploadDocument(body: {
  filename: string;
  content: string;
}): Promise<Document> {
  return apiJson<Document>("/api/v1/documents", {
    method: "POST",
    body: JSON.stringify(body),
  });
}
