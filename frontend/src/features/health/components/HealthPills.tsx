import type { Health } from "../types";
import { cn } from "@/lib/utils";

type HealthPillsProps = {
  health: Health | null;
};

// ────────────────────────────────────────────────────────
// HealthPills
// Feature: health
// Endpoint: GET /health
// Use: show llm, postgres, and redis status in the sidebar.
// ────────────────────────────────────────────────────────

export function HealthPills({ health }: HealthPillsProps) {
  const pill = (ok: boolean, label: string) => (
    <span
      className={cn(
        "rounded-full border px-2 py-0.5 text-[11px]",
        ok ? "border-[#245c43] text-ok" : "border-line text-warn",
      )}
    >
      {label}
    </span>
  );

  return (
    <div className="mt-2.5 flex flex-wrap gap-2">
      {pill(Boolean(health?.llm && health.llm !== "demo"), health?.llm || "llm")}
      {pill(Boolean(health?.postgres), "postgres")}
      {pill(Boolean(health?.redis), "redis")}
    </div>
  );
}
