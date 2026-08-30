"use client";

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
// Feature: auth
// Use: wrap the app and expose session state to all features.
// ────────────────────────────────────────────────────────

export function AuthProvider({ children }: { children: ReactNode }) {
  const [authReady, setAuthReady] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [userEmail, setUserEmail] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const profile = await fetchCurrentUser();
        if (cancelled) return;
        setIsAuthenticated(true);
        setUserEmail(profile.email);
      } catch {
        if (!cancelled) setIsAuthenticated(false);
      } finally {
        if (!cancelled) setAuthReady(true);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    setError(null);
    const token = await loginUser({ email, password });
    setIsAuthenticated(true);
    setUserEmail(token.email);
  }, []);

  const register = useCallback(
    async (email: string, password: string, name: string) => {
      setError(null);
      const token = await registerUser({ email, password, name });
      setIsAuthenticated(true);
      setUserEmail(token.email);
    },
    [],
  );

  const logout = useCallback(async () => {
    try {
      await logoutUser();
    } catch {
      // Clear local state even when the server logout fails.
    }
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
// Feature: auth
// Use: read login state and auth actions from any client component.
// ────────────────────────────────────────────────────────

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
