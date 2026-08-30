/**
 * Integration test — knowledge upload UI → API → document list state.
 */

import { act, renderHook, waitFor } from "@testing-library/react";

import { useDocuments } from "@/features/knowledge/hooks";

const mockListDocuments = jest.fn();
const mockUploadDocument = jest.fn();

jest.mock("@/features/knowledge/api", () => ({
  listDocuments: (...args: unknown[]) => mockListDocuments(...args),
  uploadDocument: (...args: unknown[]) => mockUploadDocument(...args),
}));

// ────────────────────────────────────────────────────────────
// knowledge upload integration
// Feature: knowledge
// Endpoint: GET /documents, POST /documents
// Use: upload form triggers API and refreshes document list.
// ────────────────────────────────────────────────────────────

describe("knowledge upload integration", () => {
  beforeEach(() => {
    mockListDocuments.mockReset();
    mockUploadDocument.mockReset();
    mockListDocuments
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce([
        { id: "new-doc", filename: "handbook.md", created_at: "2026-01-01" },
      ]);
    mockUploadDocument.mockResolvedValue({
      id: "new-doc",
      filename: "handbook.md",
      created_at: "2026-01-01T00:00:00Z",
    });
  });

  it("uploads then reloads documents from API", async () => {
    const { result } = renderHook(() => useDocuments());

    await waitFor(() => {
      expect(result.current.documents).toEqual([]);
    });

    act(() => {
      result.current.setFilename("handbook.md");
      result.current.setContent("Leave policy: 14 days");
    });

    await act(async () => {
      await result.current.submitUpload();
    });

    expect(mockUploadDocument).toHaveBeenCalledWith({
      filename: "handbook.md",
      content: "Leave policy: 14 days",
    });

    await waitFor(() => {
      expect(result.current.documents).toHaveLength(1);
      expect(result.current.documents[0].filename).toBe("handbook.md");
    });
  });
});
