// Minimal className joiner — avoids adding a new dependency (clsx/cva) for
// something this small. Falsy values are skipped so conditional classes
// read naturally: cn("a", condition && "b", props.className).
export function cn(...classes: Array<string | false | null | undefined>): string {
  return classes.filter(Boolean).join(" ");
}
