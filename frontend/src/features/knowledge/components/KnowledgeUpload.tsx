"use client";

import { FormEvent } from "react";

import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";

type KnowledgeUploadProps = {
  filename: string;
  content: string;
  uploading: boolean;
  onFilenameChange: (value: string) => void;
  onContentChange: (value: string) => void;
  onSubmit: (event: FormEvent) => void;
};

// ────────────────────────────────────────────────────────
// KnowledgeUpload
// Feature: knowledge
// Endpoint: POST /documents
// Use: upload form — filename and text content for RAG.
// ────────────────────────────────────────────────────────

export function KnowledgeUpload({
  filename,
  content,
  uploading,
  onFilenameChange,
  onContentChange,
  onSubmit,
}: KnowledgeUploadProps) {
  return (
    <form className="flex flex-col gap-2 border-t border-line pt-4" onSubmit={onSubmit}>
      <strong className="text-xs">Upload document</strong>
      <Input
        value={filename}
        onChange={(e) => onFilenameChange(e.target.value)}
        placeholder="filename.md"
        required
      />
      <textarea
        className="w-full resize-y rounded-[10px] border border-line bg-panel px-3 py-2 text-text placeholder:text-muted focus:outline-none focus:ring-2 focus:ring-accent/40"
        value={content}
        onChange={(e) => onContentChange(e.target.value)}
        placeholder="Paste knowledge for RAG..."
        rows={6}
        required
      />
      <Button type="submit" variant="ghost" disabled={uploading}>
        {uploading ? "Uploading…" : "Upload"}
      </Button>
    </form>
  );
}
