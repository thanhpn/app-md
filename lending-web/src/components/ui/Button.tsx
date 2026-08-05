import { forwardRef, type ButtonHTMLAttributes } from "react";
import { cn } from "./cn";
import { controlHeight, buttonPaddingX, controlFontSize, type ControlSize } from "./sizes";

export type ButtonVariant = "primary" | "accent" | "secondary" | "ghost" | "danger";

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ControlSize;
}

// variant controls color/background/border ONLY — size controls height/
// padding/font-size ONLY, so any two buttons of the same size are always
// the same height as an Input/Select of that size.
const variantClasses: Record<ButtonVariant, string> = {
  primary: "bg-brand text-white hover:bg-brand-dark shadow-sm shadow-brand/20",
  accent: "bg-accent text-white hover:bg-accent-dark shadow-sm shadow-accent/25",
  secondary: "bg-white text-ink border border-line hover:border-brand hover:text-brand",
  ghost: "bg-transparent text-ink-soft hover:bg-brand-light hover:text-brand",
  danger: "bg-danger text-white hover:bg-danger-dark",
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = "primary", size = "md", className, type = "button", ...props }, ref) => (
    <button
      ref={ref}
      type={type}
      className={cn(
        "inline-flex items-center justify-center rounded-xl font-semibold tracking-tight transition-colors whitespace-nowrap",
        "disabled:opacity-50 disabled:cursor-not-allowed",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand focus-visible:ring-offset-2",
        controlHeight[size],
        buttonPaddingX[size],
        controlFontSize[size],
        variantClasses[variant],
        className,
      )}
      {...props}
    />
  ),
);
Button.displayName = "Button";
