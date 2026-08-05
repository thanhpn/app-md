// Shared size scale for every interactive control (Button/Input/Select/
// Textarea) — height is an EXPLICIT class, never derived from padding+
// border, so a borderless Button and a bordered Input of the same size
// always render at the exact same pixel height.
export type ControlSize = "sm" | "md" | "lg";

export const controlHeight: Record<ControlSize, string> = {
  sm: "h-9",
  md: "h-10",
  lg: "h-12",
};

export const inputPaddingX: Record<ControlSize, string> = {
  sm: "px-3",
  md: "px-4",
  lg: "px-5",
};

export const buttonPaddingX: Record<ControlSize, string> = {
  sm: "px-4",
  md: "px-5",
  lg: "px-7",
};

export const controlFontSize: Record<ControlSize, string> = {
  sm: "text-sm",
  md: "text-sm",
  lg: "text-base",
};

// Textarea is multi-line, so it uses min-height instead of a fixed height.
export const textareaMinHeight: Record<ControlSize, string> = {
  sm: "min-h-20",
  md: "min-h-24",
  lg: "min-h-28",
};
