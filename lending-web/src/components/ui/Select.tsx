import { forwardRef, type SelectHTMLAttributes } from "react";
import { cn } from "./cn";
import { controlHeight, inputPaddingX, controlFontSize, type ControlSize } from "./sizes";

export interface SelectProps extends Omit<SelectHTMLAttributes<HTMLSelectElement>, "size"> {
  size?: ControlSize;
}

export const Select = forwardRef<HTMLSelectElement, SelectProps>(({ size = "md", className, children, ...props }, ref) => (
  <select
    ref={ref}
    className={cn(
      "rounded-lg border border-line bg-white text-ink",
      "focus:outline-none focus:border-brand focus:ring-2 focus:ring-brand/10",
      "disabled:opacity-50 disabled:cursor-not-allowed",
      controlHeight[size],
      inputPaddingX[size],
      controlFontSize[size],
      className,
    )}
    {...props}
  >
    {children}
  </select>
));
Select.displayName = "Select";
