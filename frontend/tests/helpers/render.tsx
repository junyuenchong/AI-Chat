/**
 * Test render helpers with providers.
 */

import { render, type RenderOptions } from "@testing-library/react";
import type { ReactElement, ReactNode } from "react";

import { AuthProvider } from "@/features/auth/AuthProvider";

// ────────────────────────────────────────────────────────────
// AllProviders
// Feature: test helpers
// Use: wrap components with AuthProvider for integration tests.
// ────────────────────────────────────────────────────────────

function AllProviders({ children }: { children: ReactNode }) {
  return <AuthProvider>{children}</AuthProvider>;
}

// ────────────────────────────────────────────────────────────
// renderWithProviders
// Feature: test helpers
// Use: render a component with app providers (auth session).
// ────────────────────────────────────────────────────────────

export function renderWithProviders(ui: ReactElement, options?: RenderOptions) {
  return render(ui, { wrapper: AllProviders, ...options });
}
