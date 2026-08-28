"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";

import { listDocuments, uploadDocument } from "./api";
import type { Document } from "./types";

// ────────────────────────────────────────────────────────
// useDocuments
// Feature: knowledge
// Endpoint: GET /documents, POST /documents
// Use: list and upload knowledge-base documents for RAG.
// ────────────────────────────────────────────────────────

export function useDocuments() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [filename, setFilename] = useState("notes.md");
  const [content, setContent] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);

  const refresh = useCallback(async () => {
    try {
      const rows = await listDocuments();
      setDocuments(rows);
      setError(null);
    } catch {
      setDocuments([]);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const submitUpload = useCallback(
    async (event?: FormEvent) => {
      event?.preventDefault();
      if (uploading) return;
      setUploading(true);
      setError(null);
      try {
        await uploadDocument({ filename, content });
        setContent("");
        await refresh();
      } catch (err) {
        setError(err instanceof Error ? err.message : "Could not upload document.");
      } finally {
        setUploading(false);
      }
    },
    [uploading, filename, content, refresh],
  );

  return {
    documents,
    filename,
    setFilename,
    content,
    setContent,
    error,
    uploading,
    refresh,
    submitUpload,
  };
}
