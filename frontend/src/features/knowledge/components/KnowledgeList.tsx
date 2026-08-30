import { KnowledgeItem } from "./KnowledgeItem";
import type { Document } from "../types";

type KnowledgeListProps = {
  documents: Document[];
};

// ────────────────────────────────────────────────────────
// KnowledgeList
// Feature: knowledge
// Endpoint: GET /documents
// Use: display all uploaded RAG documents.
// ────────────────────────────────────────────────────────

export function KnowledgeList({ documents }: KnowledgeListProps) {
  if (!documents.length) {
    return (
      <p className="text-xs text-muted">
        No documents yet. Upload text below for RAG search.
      </p>
    );
  }
  return (
    <div className="flex flex-col gap-2">
      {documents.map((doc) => (
        <KnowledgeItem key={doc.id} document={doc} />
      ))}
    </div>
  );
}
