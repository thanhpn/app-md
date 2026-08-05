import { forwardRef, type InputHTMLAttributes } from "react";
import { cn } from "./cn";
import { controlHeight, inputPaddingX, controlFontSize, type ControlSize } from "./sizes";

export interface InputProps extends Omit<InputHTMLAttributes<HTMLInputElement>, "size"> {
  size?: ControlSize;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(({ size = "md", className, ...props }, ref) => (
  <input
    ref={ref}
    className={cn(
      "w-full rounded-lg border border-line bg-white text-ink placeholder:text-ink-faint",
      "focus:outline-none focus:border-brand focus:ring-2 focus:ring-brand/10",
      "disabled:opacity-50 disabled:cursor-not-allowed",
      controlHeight[size],
      inputPaddingX[size],
      controlFontSize[size],
      className,
    )}
    {...props}
  />
));
Input.displayName = "Input";
