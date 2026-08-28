import { AuthForm } from "@/features/auth/components/AuthForm";

// ────────────────────────────────────────────────────────
// RegisterPage
// Feature: auth
// Endpoint: POST /auth/register
// Use: sign-up route for new users.
// ────────────────────────────────────────────────────────

export default function RegisterPage() {
  return <AuthForm mode="register" />;
}
