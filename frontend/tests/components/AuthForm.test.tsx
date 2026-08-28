/**
 * Component tests for AuthForm — login and register UI.
 */

import { fireEvent, render, screen } from "@testing-library/react";

import { AuthForm } from "@/features/auth/components/AuthForm";

import { mockAuthContext } from "../helpers/mocks";

jest.mock("@/features/auth/AuthProvider", () => ({
  useAuth: () => mockAuthContext,
}));

const mockSubmit = jest.fn().mockResolvedValue(undefined);

jest.mock("@/features/auth/hooks", () => ({
  useAuthForm: (mode: string) => ({
    email: "",
    setEmail: jest.fn(),
    password: "",
    setPassword: jest.fn(),
    name: "",
    setName: jest.fn(),
    busy: false,
    error: null,
    submit: mockSubmit,
    clearError: jest.fn(),
    mode,
  }),
}));

// ────────────────────────────────────────────────────────────
// AuthForm
// Feature: auth
// Endpoint: POST /auth/login, POST /auth/register
// Use: render sign-in and sign-up forms with submit button.
// ────────────────────────────────────────────────────────────

describe("AuthForm", () => {
  beforeEach(() => {
    mockSubmit.mockClear();
  });

  it("renders login title and submit button", () => {
    render(<AuthForm mode="login" />);
    expect(screen.getByRole("heading", { name: /sign in/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /sign in/i })).toBeInTheDocument();
  });

  it("renders register title", () => {
    render(<AuthForm mode="register" />);
    expect(screen.getByRole("heading", { name: /create account/i })).toBeInTheDocument();
  });

  it("calls submit when form is submitted", () => {
    render(<AuthForm mode="login" />);
    fireEvent.submit(screen.getByRole("button", { name: /sign in/i }).closest("form")!);
    expect(mockSubmit).toHaveBeenCalled();
  });
});
