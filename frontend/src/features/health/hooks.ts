"use client";

import { useCallback, useEffect, useState } from "react";

import { fetchHealth } from "./api";
import type { Health } from "./types";

// ────────────────────────────────────────────────────────
// useHealth
// Feature: health
// Endpoint: GET /health
// Use: poll backend health for LLM, Postgres, and Redis status pills.
// ────────────────────────────────────────────────────────

export function useHealth() {
  const [health, setHealth] = useState<Health | null>(null);

  const refresh = useCallback(async () => {
    try {
      const data = await fetchHealth();
      setHealth(data);
    } catch {
      setHealth(null);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return { health, refresh };
}
