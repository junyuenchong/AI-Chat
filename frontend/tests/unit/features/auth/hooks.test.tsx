/**
 * Unit tests for features/auth/hooks.ts — useAuthForm.
 */

import { act, renderHook } from "@testing-library/react";

import { useAuthForm } from "@/features/auth/hooks";

import { mockAuthContext } from "../../../helpers/mocks";

jest.mock("@/features/auth/AuthProvider", () => ({
  useAuth: () => mockAuthContext,
}));

// ────────────────────────────────────────────────────────────
// useAuthForm
// Feature: auth
// Endpoint: POST /auth/login, POST /auth/register
// Use: manage form state and call login/register on submit.
// ────────────────────────────────────────────────────────────

describe("useAuthForm", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockAuthContext.error = null;
  });

  it("calls login on submit in login mode", async () => {
    const { result } = renderHook(() => useAuthForm("login"));

    act(() => {
      result.current.setEmail("a@b.com");
      result.current.setPassword("secret12");
    });

    await act(async () => {
      await result.current.submit();
    });

    expect(mockAuthContext.login).toHaveBeenCalledWith("a@b.com", "secret12");
    expect(result.current.password).toBe(""); // Cleared after success.
  });

  it("calls register on submit in register mode", async () => {
    const { result } = renderHook(() => useAuthForm("register"));

    act(() => {
      result.current.setEmail("a@b.com");
      result.current.setPassword("secret12");
      result.current.setName("Ada");
    });

    await act(async () => {
      await result.current.submit();
    });

    expect(mockAuthContext.register).toHaveBeenCalledWith("a@b.com", "secret12", "Ada");
  });

  it("surfaces local error when login throws", async () => {
    mockAuthContext.login.mockRejectedValueOnce(new Error("Invalid credentials"));
    const { result } = renderHook(() => useAuthForm("login"));

    act(() => {
      result.current.setEmail("a@b.com");
      result.current.setPassword("bad");
    });

    await act(async () => {
      await result.current.submit();
    });

    expect(result.current.error).toBe("Invalid credentials");
  });
});
