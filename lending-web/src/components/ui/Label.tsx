import { forwardRef, type LabelHTMLAttributes } from "react";
import { cn } from "./cn";

export const Label = forwardRef<HTMLLabelElement, LabelHTMLAttributes<HTMLLabelElement>>(
  ({ className, ...props }, ref) => (
    <label ref={ref} className={cn("block text-sm font-medium text-ink-soft mb-1.5", className)} {...props} />
  ),
);
Label.displayName = "Label";
