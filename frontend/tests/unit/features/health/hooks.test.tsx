/**
 * Unit tests for features/health/hooks.ts — useHealth.
 */

import { renderHook, waitFor } from "@testing-library/react";

import { useHealth } from "@/features/health/hooks";

jest.mock("@/features/health/api", () => ({
  fetchHealth: jest.fn().mockResolvedValue({
    status: "ok",
    llm: "ok",
    postgres: "ok",
    redis: "ok",
  }),
}));

// ────────────────────────────────────────────────────────────
// useHealth
// Feature: health
// Endpoint: GET /health
// Use: poll backend dependency status on mount.
// ────────────────────────────────────────────────────────────

describe("useHealth", () => {
  it("loads health status on mount", async () => {
    const { result } = renderHook(() => useHealth());

    await waitFor(() => {
      expect(result.current.health).toEqual({
        status: "ok",
        llm: "ok",
        postgres: "ok",
        redis: "ok",
      });
    });
  });

  it("sets health to null when API fails", async () => {
    const { fetchHealth } = await import("@/features/health/api");
    (fetchHealth as jest.Mock).mockRejectedValue(new Error("offline"));

    const { result } = renderHook(() => useHealth());

    await waitFor(() => {
      expect(result.current.health).toBeNull();
    });
  });
});
