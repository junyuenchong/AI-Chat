import type { ButtonHTMLAttributes, ReactNode } from "react";

import { cn } from "@/lib/utils";

type ButtonVariant = "primary" | "ghost";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  children: ReactNode;
  variant?: ButtonVariant;
};

const variantClasses: Record<ButtonVariant, string> = {
  primary: "bg-accent text-accent-fg border-0",
  ghost: "bg-transparent text-text border border-line",
};

// ────────────────────────────────────────────────────────
// Button
// Feature: ui (shared)
// Use: primary action button used across all features.
// ────────────────────────────────────────────────────────

export function Button({
  children,
  className,
  variant = "primary",
  ...props
}: ButtonProps) {
  return (
    <button
      className={cn(
        "rounded-[10px] px-3 py-2 text-sm font-semibold cursor-pointer",
        "disabled:opacity-55 disabled:cursor-not-allowed",
        variantClasses[variant],
        className,
      )}
      {...props}
    >
      {children}
    </button>
  );
}
