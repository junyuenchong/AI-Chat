"use client";

/**
 * Auth route layout — centered login/register pages.
 *
 * Request path:
 *   app/(auth)/layout.tsx
 *     → AuthLayout.tsx  (this file)
 *     → redirects to /chat when already signed in
 */

import { useRouter } from "next/navigation";
import { useEffect, type ReactNode } from "react";

import { Loading } from "@/components/ui/Loading";
import { useAuth } from "@/features/auth/AuthProvider";

// ────────────────────────────────────────────────────────
// AuthLayout
// Feature: auth
// Use: centered layout for login/register — redirect if already signed in.
// ────────────────────────────────────────────────────────

export function AuthLayout({ children }: { children: ReactNode }) {
  const { authReady, isAuthenticated } = useAuth();
  const router = useRouter();

  useEffect(() => {
    // Step 1 — skip login page when JWT session is already valid.
    if (authReady && isAuthenticated) {
      router.replace("/chat");
    }
  }, [authReady, isAuthenticated, router]);

  if (!authReady) return <Loading />;
  if (isAuthenticated) return <Loading label="Redirecting…" />;

  return (
    <div className="flex min-h-dvh items-center justify-center p-4 sm:p-6">{children}</div>
  );
}
