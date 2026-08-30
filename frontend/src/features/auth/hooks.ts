"use client";

/**
 * Auth form hook — login and register field state + submit handler.
 *
 * Request path:
 *   features/auth/components/AuthForm.tsx
 *     → features/auth/hooks.ts  (this file)
 *     → features/auth/AuthProvider.tsx
 */

import { useState } from "react";

import type { AuthMode } from "./types";
import { useAuth } from "./AuthProvider";

// ────────────────────────────────────────────────────────
// useAuthForm
// Feature: auth
// Endpoint: POST /auth/login, POST /auth/register
// Use: manage login/register form fields and submit handler.
// ────────────────────────────────────────────────────────

export function useAuthForm(mode: AuthMode) {
  const { login, register, error, clearError } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [busy, setBusy] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  const submit = async () => {
    if (busy) return;
    setBusy(true);
    setLocalError(null);
    clearError();
    try {
      // Step 1 — call register or login via AuthProvider.
      if (mode === "register") {
        await register(email, password, name);
      } else {
        await login(email, password);
      }
      // Step 2 — clear password field after success.
      setPassword("");
    } catch (err) {
      setLocalError(err instanceof Error ? err.message : "Could not sign in.");
    } finally {
      setBusy(false);
    }
  };

  return {
    email,
    setEmail,
    password,
    setPassword,
    name,
    setName,
    busy,
    error: localError || error,
    submit,
    clearError: () => {
      setLocalError(null);
      clearError();
    },
  };
}
