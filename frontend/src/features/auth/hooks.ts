"use client";

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
      if (mode === "register") {
        await register(email, password, name);
      } else {
        await login(email, password);
      }
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
