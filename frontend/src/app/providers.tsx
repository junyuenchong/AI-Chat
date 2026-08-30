"use client";

/**
 * Root app providers — wraps all routes with auth context.
 *
 * Request path:
 *   app/layout.tsx
 *     → app/providers.tsx  (this file)
 *     → features/auth/AuthProvider.tsx
 */

import type { ReactNode } from "react";

import { AuthProvider } from "@/features/auth/AuthProvider";

// ────────────────────────────────────────────────────────
// AppProviders
// Feature: shared
// Use: wrap the app with auth context for all routes.
// ────────────────────────────────────────────────────────

export function AppProviders({ children }: { children: ReactNode }) {
  return <AuthProvider>{children}</AuthProvider>;
}
