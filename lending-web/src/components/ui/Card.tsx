import type { HTMLAttributes } from "react";
import { cn } from "./cn";

export interface CardProps extends HTMLAttributes<HTMLDivElement> {
  padding?: "sm" | "md" | "lg";
  hover?: boolean;
}

const paddingClasses: Record<NonNullable<CardProps["padding"]>, string> = {
  sm: "p-4",
  md: "p-6",
  lg: "p-8",
};

export function Card({ padding = "md", hover = false, className, ...props }: CardProps) {
  return (
    <div
      className={cn(
        "bg-surface border border-line rounded-2xl",
        hover && "transition-all hover:shadow-lg hover:shadow-ink/5 hover:-translate-y-0.5",
        paddingClasses[padding],
        className,
      )}
      {...props}
    />
  );
}
