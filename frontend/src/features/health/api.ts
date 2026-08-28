import { apiJson } from "@/lib/api/client";

import type { Health } from "./types";

// ────────────────────────────────────────────────────────
// fetchHealth
// Feature: health
// Endpoint: GET /health
// Use: load API status and dependency flags for the header pills.
// ────────────────────────────────────────────────────────

export async function fetchHealth(): Promise<Health> {
  return apiJson<Health>("/api/v1/health");
}
