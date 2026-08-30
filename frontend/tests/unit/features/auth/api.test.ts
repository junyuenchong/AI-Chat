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

  it("fetchCurrentUser calls GET /auth/me", async () => {
    (global.fetch as jest.Mock).mockResolvedValue(
      jsonResponse({ id: "u1", email: "a@b.com", name: "Ada" }),
    );
    const user = await fetchCurrentUser();
    expect(user.email).toBe("a@b.com");
  });

  it("logoutUser calls POST /auth/logout", async () => {
    (global.fetch as jest.Mock).mockResolvedValue(new Response(null, { status: 204 }));
    await logoutUser();
    expect(global.fetch).toHaveBeenCalledWith(
      "/api/v1/auth/logout",
      expect.objectContaining({ method: "POST" }),
    );
  });
});
