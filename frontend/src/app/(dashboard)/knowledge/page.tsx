"use client";

import { KnowledgeList } from "@/features/knowledge/components/KnowledgeList";
import { KnowledgeUpload } from "@/features/knowledge/components/KnowledgeUpload";
import { useDocuments } from "@/features/knowledge/hooks";

// ────────────────────────────────────────────────────────
// KnowledgePage
// Feature: knowledge
// Endpoint: GET /documents, POST /documents
// Use: knowledge page — list and upload RAG documents.
// ────────────────────────────────────────────────────────

export default function KnowledgePage() {
  const {
    documents,
    filename,
    setFilename,
    content,
    setContent,
    error,
    uploading,
    submitUpload,
  } = useDocuments();

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <header className="flex shrink-0 items-start justify-between gap-3 border-b border-line px-4 py-3 sm:px-5 sm:py-3.5">
        <div className="min-w-0">
          <strong className="block text-sm">Knowledge base</strong>
          <span className="text-xs text-muted">
            Upload text the AI can search during chat (RAG)
          </span>
        </div>
      </header>
      <div className="flex min-h-0 flex-1 flex-col gap-4 overflow-auto p-4 sm:p-5">
        <KnowledgeList documents={documents} />
        {error ? <div className="text-xs text-warn">{error}</div> : null}
        <KnowledgeUpload
          filename={filename}
          content={content}
          uploading={uploading}
          onFilenameChange={setFilename}
          onContentChange={setContent}
          onSubmit={submitUpload}
        />
      </div>
    </div>
  );
}
