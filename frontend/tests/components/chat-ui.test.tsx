/**
 * Component tests for chat UI — MessageList and ChatInput.
 */

import { createRef } from "react";
import { fireEvent, render, screen } from "@testing-library/react";

import { ChatInput } from "@/features/chat/components/ChatInput";
import { MessageList } from "@/features/chat/components/MessageList";

// ────────────────────────────────────────────────────────────
// MessageList
// Feature: chat
// Use: render user and assistant bubbles; show typing indicator while streaming.
// ────────────────────────────────────────────────────────────

describe("MessageList", () => {
  it("renders user and assistant messages", () => {
    const ref = createRef<HTMLDivElement>();
    render(
      <MessageList
        bubbles={[
          { role: "user", content: "Hello" },
          { role: "assistant", content: "Hi there" },
        ]}
        streaming={false}
        messagesRef={ref}
      />,
    );
    expect(screen.getByText("Hello")).toBeInTheDocument();
    expect(screen.getByText("Hi there")).toBeInTheDocument();
  });

  it("shows typing indicator on empty streaming assistant bubble", () => {
    const ref = createRef<HTMLDivElement>();
    render(
      <MessageList
        bubbles={[{ role: "assistant", content: "" }]}
        streaming={true}
        messagesRef={ref}
      />,
    );
    expect(screen.getByText(/thinking/i)).toBeInTheDocument();
  });
});

// ────────────────────────────────────────────────────────────
// ChatInput
// Feature: chat
// Endpoint: POST /chat/stream
// Use: message composer with disabled state while streaming.
// ────────────────────────────────────────────────────────────

describe("ChatInput", () => {
  it("disables send when streaming", () => {
    render(
      <ChatInput value="hi" streaming={true} onChange={jest.fn()} onSubmit={jest.fn()} />,
    );
    expect(screen.getByRole("button", { name: /sending/i })).toBeDisabled();
  });

  it("calls onSubmit when form is submitted", () => {
    const onSubmit = jest.fn((e) => e.preventDefault());
    render(
      <ChatInput value="hello" streaming={false} onChange={jest.fn()} onSubmit={onSubmit} />,
    );
    fireEvent.submit(screen.getByRole("button", { name: /send/i }).closest("form")!);
    expect(onSubmit).toHaveBeenCalled();
  });
});
