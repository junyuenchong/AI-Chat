/**
 * Unit tests for features/health/hooks.ts — useHealth.
 */

import { renderHook, waitFor } from "@testing-library/react";

import { useHealth } from "@/features/health/hooks";

jest.mock("@/features/health/api", () => ({
  fetchHealth: jest.fn().mockResolvedValue({
    status: "ok",
    app: "AI Chat",
    llm: "demo",
    postgres: true,
  }),
}));

describe("useHealth", () => {
  it("loads health status on mount", async () => {
    const { result } = renderHook(() => useHealth());

    await waitFor(() => {
      expect(result.current.health).toEqual({
        status: "ok",
        app: "AI Chat",
        llm: "demo",
        postgres: true,
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
