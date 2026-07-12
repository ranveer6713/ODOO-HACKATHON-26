import { cn } from "@/lib/utils";
import { TONE_CLASSES, type StatusMeta, type Tone } from "@/lib/constants";

interface StatusBadgeProps {
  meta?: StatusMeta;
  tone?: Tone;
  label?: string;
  dot?: boolean;
  className?: string;
}

export function StatusBadge({ meta, tone, label, dot = true, className }: StatusBadgeProps) {
  const resolvedTone = meta?.tone ?? tone ?? "neutral";
  const resolvedLabel = meta?.label ?? label ?? "—";
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-md px-2 py-0.5 text-xs font-medium ring-1 ring-inset",
        TONE_CLASSES[resolvedTone],
        className,
      )}
    >
      {dot && (
        <span
          className={cn("size-1.5 rounded-full", {
            "bg-muted-foreground": resolvedTone === "neutral",
            "bg-primary": resolvedTone === "primary",
            "bg-success": resolvedTone === "success",
            "bg-warning": resolvedTone === "warning",
            "bg-destructive": resolvedTone === "danger",
            "bg-blue-500": resolvedTone === "info",
            "bg-violet-500": resolvedTone === "purple",
          })}
        />
      )}
      {resolvedLabel}
    </span>
  );
}
