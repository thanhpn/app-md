import { forwardRef, type TextareaHTMLAttributes } from "react";
import { cn } from "./cn";
import { inputPaddingX, controlFontSize, textareaMinHeight, type ControlSize } from "./sizes";

export interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  size?: ControlSize;
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(({ size = "md", className, ...props }, ref) => (
  <textarea
    ref={ref}
    className={cn(
      "w-full rounded-lg border border-line bg-white text-ink placeholder:text-ink-faint py-2",
      "focus:outline-none focus:border-brand focus:ring-2 focus:ring-brand/10",
      "disabled:opacity-50 disabled:cursor-not-allowed",
      textareaMinHeight[size],
      inputPaddingX[size],
      controlFontSize[size],
      className,
    )}
    {...props}
  />
));
Textarea.displayName = "Textarea";
