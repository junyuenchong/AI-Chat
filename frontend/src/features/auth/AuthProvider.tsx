"use client";

/**
 * Auth context — JWT session state for the whole app.
 *
 * Request path:
 *   app/providers.tsx
 *     → features/auth/AuthProvider.tsx  (this file)
 *     → features/auth/api.ts
 */

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import { fetchCurrentUser, loginUser, logoutUser, registerUser } from "./api";

type AuthContextValue = {
  authReady: boolean;
  isAuthenticated: boolean;
  userEmail: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, name: string) => Promise<void>;
  logout: () => Promise<void>;
  error: string | null;
  clearError: () => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);

// ────────────────────────────────────────────────────────
// AuthProvider
// Path: features/auth/AuthProvider.tsx
// Use: wrap the app and expose login state to all features.
// ────────────────────────────────────────────────────────
export function AuthProvider({ children }: { children: ReactNode }) {
  const [authReady, setAuthReady] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [userEmail, setUserEmail] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Step 1 — on mount, restore session from JWT in sessionStorage.
  useEffect(() => {
    let cancelled = false;
    (async () => {
      const profile = await fetchCurrentUser();
      if (cancelled) return;
      if (profile) {
        setIsAuthenticated(true);
        setUserEmail(profile.email);
      } else {
        setIsAuthenticated(false);
        setUserEmail(null);
      }
      setAuthReady(true);
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  // ────────────────────────────────────────────────────────
  // login
  // Endpoint: POST /auth/login
  // ────────────────────────────────────────────────────────
  const login = useCallback(async (email: string, password: string) => {
    setError(null);
    const token = await loginUser({ email, password });
    setIsAuthenticated(true);
    setUserEmail(token.email);
  }, []);

  // ────────────────────────────────────────────────────────
  // register
  // Endpoint: POST /auth/register
  // ────────────────────────────────────────────────────────
  const register = useCallback(
    async (email: string, password: string, name: string) => {
      setError(null);
      const token = await registerUser({ email, password, name });
      setIsAuthenticated(true);
      setUserEmail(token.email);
    },
    [],
  );

  // ────────────────────────────────────────────────────────
  // logout
  // Use: clear JWT and local auth state.
  // ────────────────────────────────────────────────────────
  const logout = useCallback(async () => {
    await logoutUser();
    setIsAuthenticated(false);
    setUserEmail(null);
    setError(null);
  }, []);

  const value = useMemo(
    () => ({
      authReady,
      isAuthenticated,
      userEmail,
      login,
      register,
      logout,
      error,
      clearError: () => setError(null),
    }),
    [authReady, isAuthenticated, userEmail, login, register, logout, error],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// ────────────────────────────────────────────────────────
// useAuth
// Path: features/auth/AuthProvider.tsx
// Use: read login state and auth actions from any client component.
// ────────────────────────────────────────────────────────
export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
