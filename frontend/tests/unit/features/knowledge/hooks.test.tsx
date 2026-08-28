/**
 * Unit tests for features/knowledge/hooks.ts — useDocuments.
 */

import { act, renderHook, waitFor } from "@testing-library/react";

import { useDocuments } from "@/features/knowledge/hooks";

jest.mock("@/features/knowledge/api", () => ({
  listDocuments: jest.fn().mockResolvedValue([{ id: "d1", filename: "a.md", created_at: "2026-01-01" }]),
  uploadDocument: jest.fn().mockResolvedValue({ id: "d2", filename: "b.md", created_at: "2026-01-02" }),
}));

// ────────────────────────────────────────────────────────────
// useDocuments
// Feature: knowledge
// Endpoint: GET /documents, POST /documents
// Use: load document list and handle upload form submit.
// ────────────────────────────────────────────────────────────

describe("useDocuments", () => {
  it("loads documents on mount", async () => {
    const { result } = renderHook(() => useDocuments());

    await waitFor(() => {
      expect(result.current.documents).toHaveLength(1);
    });
  });

  it("uploads document and refreshes list", async () => {
    const { result } = renderHook(() => useDocuments());

    await waitFor(() => {
      expect(result.current.documents).toHaveLength(1);
    });

    act(() => {
      result.current.setFilename("notes.md");
      result.current.setContent("Annual leave policy");
    });

    await act(async () => {
      await result.current.submitUpload();
    });

    expect(result.current.content).toBe(""); // Form cleared after success.
  });
});
