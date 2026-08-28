/**
 * Component tests for knowledge UI — list and upload form.
 */

import { fireEvent, render, screen } from "@testing-library/react";

import { KnowledgeList } from "@/features/knowledge/components/KnowledgeList";
import { KnowledgeUpload } from "@/features/knowledge/components/KnowledgeUpload";

// ────────────────────────────────────────────────────────────
// KnowledgeList
// Feature: knowledge
// Endpoint: GET /documents
// Use: show uploaded documents or empty state.
// ────────────────────────────────────────────────────────────

describe("KnowledgeList", () => {
  it("shows empty hint when no documents", () => {
    render(<KnowledgeList documents={[]} />);
    expect(screen.getByText(/no documents yet/i)).toBeInTheDocument();
  });

  it("renders document filenames", () => {
    render(
      <KnowledgeList
        documents={[{ id: "d1", filename: "policy.md", created_at: "2026-01-01T00:00:00Z" }]}
      />,
    );
    expect(screen.getByText("policy.md")).toBeInTheDocument();
  });
});

// ────────────────────────────────────────────────────────────
// KnowledgeUpload
// Feature: knowledge
// Endpoint: POST /documents
// Use: filename and content fields with upload button.
// ────────────────────────────────────────────────────────────

describe("KnowledgeUpload", () => {
  it("renders upload form fields", () => {
    render(
      <KnowledgeUpload
        filename="notes.md"
        content="text"
        uploading={false}
        onFilenameChange={jest.fn()}
        onContentChange={jest.fn()}
        onSubmit={jest.fn((e) => e.preventDefault())}
      />,
    );
    expect(screen.getByPlaceholderText(/filename/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /upload/i })).toBeInTheDocument();
  });

  it("disables button while uploading", () => {
    render(
      <KnowledgeUpload
        filename="notes.md"
        content="text"
        uploading={true}
        onFilenameChange={jest.fn()}
        onContentChange={jest.fn()}
        onSubmit={jest.fn()}
      />,
    );
    expect(screen.getByRole("button", { name: /uploading/i })).toBeDisabled();
  });

  it("calls onSubmit when form is submitted", () => {
    const onSubmit = jest.fn((e) => e.preventDefault());
    render(
      <KnowledgeUpload
        filename="notes.md"
        content="policy text"
        uploading={false}
        onFilenameChange={jest.fn()}
        onContentChange={jest.fn()}
        onSubmit={onSubmit}
      />,
    );
    fireEvent.submit(screen.getByRole("button", { name: /upload/i }).closest("form")!);
    expect(onSubmit).toHaveBeenCalled();
  });
});
