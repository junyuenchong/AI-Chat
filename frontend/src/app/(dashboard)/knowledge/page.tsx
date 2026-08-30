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
    <>
      <header className="flex items-center justify-between border-b border-line px-5 py-3.5">
        <div>
          <strong className="text-sm">Knowledge base</strong>
          <br />
          <span className="text-xs text-muted">
            Upload text the AI can search during chat (RAG)
          </span>
        </div>
      </header>
      <div className="flex flex-1 flex-col gap-4 overflow-auto p-5">
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
    </>
  );
}
