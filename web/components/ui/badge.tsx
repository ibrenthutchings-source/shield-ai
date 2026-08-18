import type { HTMLAttributes } from "react";

import { cn } from "@/lib/utils";

type BadgeTone = "low" | "medium" | "high" | "critical" | "neutral" | "success";

const toneClasses: Record<BadgeTone, string> = {
  low: "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300",
  medium: "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300",
  high: "bg-orange-100 text-orange-800 dark:bg-orange-950 dark:text-orange-300",
  critical: "bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300",
  neutral: "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300",
  success: "bg-sky-100 text-sky-800 dark:bg-sky-950 dark:text-sky-300",
};

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  tone?: BadgeTone;
}

export function Badge({ className, tone = "neutral", ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium",
        toneClasses[tone],
        className
      )}
      {...props}
    />
  );
}

export function severityTone(severity: string): BadgeTone {
  return severity === "low" || severity === "medium" || severity === "high" || severity === "critical"
    ? severity
    : "neutral";
}
