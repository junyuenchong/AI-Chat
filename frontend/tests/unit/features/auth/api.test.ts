/**
 * Unit tests for features/auth/api.ts
 */

import {
  fetchCurrentUser,
  loginUser,
  logoutUser,
  registerUser,
} from "@/features/auth/api";

import { jsonResponse } from "../../../helpers/mocks";

// ────────────────────────────────────────────────────────────
// auth API functions
// Feature: auth
// Endpoint: POST /auth/register, POST /auth/login, GET /auth/me, POST /auth/logout
// Use: thin wrappers around apiJson for auth routes.
// ────────────────────────────────────────────────────────────

describe("auth api", () => {
  beforeEach(() => {
    global.fetch = jest.fn();
  });

  it("registerUser posts credentials", async () => {
    (global.fetch as jest.Mock).mockResolvedValue(
      jsonResponse({
        access_token: "t",
        user_id: "u1",
        email: "a@b.com",
        name: "Ada",
        token_type: "bearer",
      }),
    );
    const res = await registerUser({
      email: "a@b.com",
      password: "secret12",
      name: "Ada",
    });
    expect(res.email).toBe("a@b.com");
    expect(global.fetch).toHaveBeenCalledWith(
      "/api/v1/auth/register",
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("loginUser posts email and password", async () => {
    (global.fetch as jest.Mock).mockResolvedValue(
      jsonResponse({
        access_token: "t",
        user_id: "u1",
        email: "a@b.com",
        name: "Ada",
        token_type: "bearer",
      }),
    );
    await loginUser({ email: "a@b.com", password: "secret12" });
    expect(global.fetch).toHaveBeenCalledWith(
      "/api/v1/auth/login",
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("fetchCurrentUser returns null when no token is stored", async () => {
    sessionStorage.clear();
    const user = await fetchCurrentUser();
    expect(user).toBeNull();
    expect(global.fetch).not.toHaveBeenCalled();
  });

  it("fetchCurrentUser calls GET /auth/me when token exists", async () => {
    sessionStorage.setItem("ai_chat_access_token", "test-token");
    (global.fetch as jest.Mock).mockResolvedValue(
      jsonResponse({ id: "u1", email: "a@b.com", name: "Ada" }),
    );
    const user = await fetchCurrentUser();
    expect(user?.email).toBe("a@b.com");
    expect(global.fetch).toHaveBeenCalledWith(
      "/api/v1/auth/me",
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: "Bearer test-token",
        }),
      }),
    );
  });

  it("fetchCurrentUser clears token on 401", async () => {
    sessionStorage.setItem("ai_chat_access_token", "stale-token");
    (global.fetch as jest.Mock).mockResolvedValue(
      jsonResponse({ error: { code: "UNAUTHORIZED", message: "Not authenticated" } }, 401),
    );
    const user = await fetchCurrentUser();
    expect(user).toBeNull();
    expect(sessionStorage.getItem("ai_chat_access_token")).toBeNull();
  });

  it("logoutUser clears stored token", async () => {
    sessionStorage.setItem("ai_chat_access_token", "test-token");
    await logoutUser();
    expect(sessionStorage.getItem("ai_chat_access_token")).toBeNull();
    expect(global.fetch).not.toHaveBeenCalled();
  });
});
