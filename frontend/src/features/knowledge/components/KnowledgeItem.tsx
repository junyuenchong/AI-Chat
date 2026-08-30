import type { Document } from "../types";

type KnowledgeItemProps = {
  document: Document;
};

// ────────────────────────────────────────────────────────
// KnowledgeItem
// Feature: knowledge
// Endpoint: GET /documents
// Use: show one uploaded document filename in the list.
// ────────────────────────────────────────────────────────

export function KnowledgeItem({ document }: KnowledgeItemProps) {
  return (
    <div className="rounded-[10px] border border-line bg-panel px-3 py-2.5">
      <strong className="block truncate text-sm">{document.filename}</strong>
      <small className="mt-1 block text-[11px] text-muted">
        {new Date(document.created_at).toLocaleString()}
      </small>
    </div>
  );
}
