"use client";

import Link from "next/link";
import { FormEvent } from "react";

import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";

import { useAuthForm } from "../hooks";
import type { AuthMode } from "../types";

type AuthFormProps = {
  mode: AuthMode;
};

// ────────────────────────────────────────────────────────
// AuthForm
// Feature: auth
// Endpoint: POST /auth/login, POST /auth/register
// Use: sign-in and sign-up forms for the auth route group.
// ────────────────────────────────────────────────────────

export function AuthForm({ mode }: AuthFormProps) {
  const { email, setEmail, password, setPassword, name, setName, busy, error, submit } =
    useAuthForm(mode);

  const onSubmit = (event: FormEvent) => {
    event.preventDefault();
    void submit();
  };

  return (
    <div className="w-full max-w-md rounded-2xl border border-line bg-panel/95 p-6">
      <h1 className="text-xl font-semibold">
        {mode === "login" ? "Sign in" : "Create account"}
      </h1>
      <p className="mt-2 text-[13px] leading-relaxed text-muted">
        HttpOnly session cookie — no token stored in localStorage.
      </p>
      <form className="mt-4 flex flex-col gap-2.5" onSubmit={onSubmit}>
        {mode === "register" ? (
          <Input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Name"
            autoComplete="name"
            required
          />
        ) : null}
        <Input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="Email"
          autoComplete="email"
          required
        />
        <Input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Password"
          autoComplete={mode === "register" ? "new-password" : "current-password"}
          minLength={mode === "register" ? 6 : 1}
          required
        />
        <Button type="submit" className="mt-1" disabled={busy}>
          {busy ? "Please wait…" : mode === "login" ? "Sign in" : "Register"}
        </Button>
      </form>
      {error ? <div className="mt-2 px-0 text-xs text-warn">{error}</div> : null}
      <div className="mt-3.5 text-center text-[13px] text-muted">
        {mode === "login" ? (
          <>
            No account?{" "}
            <Link href="/register" className="font-semibold text-accent no-underline">
              Register
            </Link>
          </>
        ) : (
          <>
            Already have an account?{" "}
            <Link href="/login" className="font-semibold text-accent no-underline">
              Sign in
            </Link>
          </>
        )}
      </div>
    </div>
  );
}
