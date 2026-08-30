// ────────────────────────────────────────────────────────
// Loading
// Feature: ui (shared)
// Use: full-screen loading state while auth session is checked.
// ────────────────────────────────────────────────────────

export function Loading({ label = "Loading…" }: { label?: string }) {
  return (
    <div className="flex min-h-dvh items-center justify-center p-4 sm:p-6">
      <div className="w-full max-w-md rounded-2xl border border-line bg-panel/95 p-6">
        <h1 className="text-xl font-semibold">AI Chat</h1>
        <p className="mt-2 text-sm leading-relaxed text-muted">{label}</p>
      </div>
    </div>
  );
}
