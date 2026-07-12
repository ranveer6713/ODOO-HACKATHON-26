import type { LucideIcon } from "lucide-react";
import { ArrowDownRight, ArrowUpRight } from "lucide-react";
import { Card } from "@/components/ui/card";
import { cn, formatNumber } from "@/lib/utils";
import type { Tone } from "@/lib/constants";

interface StatCardProps {
  label: string;
  value: number | string;
  icon: LucideIcon;
  tone?: Tone;
  hint?: string;
  trend?: { value: number; label?: string };
  className?: string;
}

const TONE_ICON: Record<Tone, string> = {
  neutral: "bg-muted text-muted-foreground",
  primary: "bg-primary/10 text-primary",
  success: "bg-success/10 text-success",
  warning: "bg-warning/15 text-warning-foreground dark:text-warning",
  danger: "bg-destructive/10 text-destructive",
  info: "bg-blue-500/10 text-blue-600 dark:text-blue-400",
  purple: "bg-violet-500/10 text-violet-600 dark:text-violet-400",
};

export function StatCard({
  label,
  value,
  icon: Icon,
  tone = "primary",
  hint,
  trend,
  className,
}: StatCardProps) {
  const up = (trend?.value ?? 0) >= 0;
  return (
    <Card className={cn("p-5", className)}>
      <div className="flex items-start justify-between">
        <div className="space-y-1">
          <p className="text-sm font-medium text-muted-foreground">{label}</p>
          <p className="text-2xl font-semibold tracking-tight text-foreground">
            {typeof value === "number" ? formatNumber(value) : value}
          </p>
        </div>
        <div className={cn("flex size-10 items-center justify-center rounded-lg", TONE_ICON[tone])}>
          <Icon className="size-5" />
        </div>
      </div>
      {(hint || trend) && (
        <div className="mt-3 flex items-center gap-2 text-xs">
          {trend && (
            <span
              className={cn(
                "inline-flex items-center gap-0.5 font-medium",
                up ? "text-success" : "text-destructive",
              )}
            >
              {up ? <ArrowUpRight className="size-3.5" /> : <ArrowDownRight className="size-3.5" />}
              {Math.abs(trend.value)}%
            </span>
          )}
          {hint && <span className="text-muted-foreground">{hint}</span>}
          {trend?.label && <span className="text-muted-foreground">{trend.label}</span>}
        </div>
      )}
    </Card>
  );
}
