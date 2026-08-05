import type { HTMLAttributes } from "react";
import { cn } from "./cn";

export type BadgeTone = "neutral" | "success" | "warning" | "danger" | "info" | "brand" | "accent";

// Always the bg-50/text-700 triad, never mix shades ad hoc.
const toneClasses: Record<BadgeTone, string> = {
  neutral: "bg-neutral-light text-ink-soft",
  success: "bg-success-light text-success",
  warning: "bg-warning-light text-warning",
  danger: "bg-danger-light text-danger",
  info: "bg-info-light text-info",
  brand: "bg-brand-light text-brand",
  accent: "bg-accent-light text-accent-dark",
};

export interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  tone?: BadgeTone;
}

export function Badge({ tone = "neutral", className, ...props }: BadgeProps) {
  return <span className={cn("inline-flex items-center rounded-full px-2.5 py-1 text-xs font-semibold", toneClasses[tone], className)} {...props} />;
}
