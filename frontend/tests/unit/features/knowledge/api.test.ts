/**
 * Unit tests for features/knowledge/api.ts
 */

import { listDocuments, uploadDocument } from "@/features/knowledge/api";

import { jsonResponse } from "../../../helpers/mocks";

// ────────────────────────────────────────────────────────────
// knowledge API
// Feature: knowledge
// Endpoint: GET /documents, POST /documents
// Use: list and upload RAG documents.
// ────────────────────────────────────────────────────────────

describe("knowledge api", () => {
  beforeEach(() => {
    global.fetch = jest.fn();
  });

  it("listDocuments returns rows", async () => {
    (global.fetch as jest.Mock).mockResolvedValue(
      jsonResponse([{ id: "d1", filename: "a.md", created_at: "2026-01-01" }]),
    );
    const rows = await listDocuments();
    expect(rows).toHaveLength(1);
    expect(global.fetch).toHaveBeenCalledWith("/api/v1/documents", expect.any(Object));
  });

  it("uploadDocument posts filename and content", async () => {
    (global.fetch as jest.Mock).mockResolvedValue(
      jsonResponse({ id: "d2", filename: "b.md", created_at: "2026-01-02" }, 201),
    );
    const doc = await uploadDocument({ filename: "b.md", content: "text" });
    expect(doc.filename).toBe("b.md");
    expect(global.fetch).toHaveBeenCalledWith(
      "/api/v1/documents",
      expect.objectContaining({ method: "POST" }),
    );
  });
});
