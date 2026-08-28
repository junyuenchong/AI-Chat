import { AuthForm } from "@/features/auth/components/AuthForm";

// ────────────────────────────────────────────────────────
// LoginPage
// Feature: auth
// Endpoint: POST /auth/login
// Use: sign-in route for existing users.
// ────────────────────────────────────────────────────────

export default function LoginPage() {
  return <AuthForm mode="login" />;
}
