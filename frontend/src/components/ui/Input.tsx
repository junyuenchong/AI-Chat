import type { InputHTMLAttributes } from "react";

import { cn } from "@/lib/utils";

type InputProps = InputHTMLAttributes<HTMLInputElement>;

// ────────────────────────────────────────────────────────
// Input
// Feature: ui (shared)
// Use: styled text input for auth and knowledge forms.
// ────────────────────────────────────────────────────────

export function Input({ className, ...props }: InputProps) {
  return (
    <input
      className={cn(
        "w-full rounded-[10px] border border-line bg-panel px-3 py-2.5 text-text",
        "placeholder:text-muted focus:outline-none focus:ring-2 focus:ring-accent/40",
        className,
      )}
      {...props}
    />
  );
}
