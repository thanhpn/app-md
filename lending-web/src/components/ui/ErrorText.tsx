import type { HTMLAttributes } from "react";
import { cn } from "./cn";

// Single shared inline-error style — used to replace ad-hoc red-* utility
// classes that had drifted into three slightly different shapes across
// pages (plain text-red-600, boxed text-red-700/bg-red-50/border-red-200).
// Always renders through the danger theme tokens (index.css) so a future
// palette change only touches one place.
export function ErrorText({ className, ...props }: HTMLAttributes<HTMLParagraphElement>) {
  return (
    <p
      className={cn("text-sm text-danger bg-danger-light border border-danger/15 rounded-lg px-3 py-2", className)}
      {...props}
    />
  );
}
