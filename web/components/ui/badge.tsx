import type { HTMLAttributes } from "react";

import { cn } from "@/lib/utils";

type BadgeTone = "low" | "medium" | "high" | "critical" | "neutral" | "success";

// Bordered, tinted-background pills (cue from dendrai-dashboard's RAG status
// badges) rather than solid-fill — reads as a status indicator, not a label.
const toneClasses: Record<BadgeTone, string> = {
  low: "border-emerald-300 bg-emerald-50 text-emerald-800 dark:border-emerald-800 dark:bg-emerald-950 dark:text-emerald-300",
  medium: "border-amber-300 bg-amber-50 text-amber-800 dark:border-amber-800 dark:bg-amber-950 dark:text-amber-300",
  high: "border-orange-300 bg-orange-50 text-orange-800 dark:border-orange-800 dark:bg-orange-950 dark:text-orange-300",
  critical: "border-red-300 bg-red-50 text-red-800 dark:border-red-800 dark:bg-red-950 dark:text-red-300",
  neutral: "border-slate-300 bg-slate-50 text-slate-700 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300",
  success:
    "border-difesa-leaf bg-difesa-cream text-difesa-forest dark:border-difesa-leaf dark:bg-slate-900 dark:text-difesa-cream",
};

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  tone?: BadgeTone;
}

export function Badge({ className, tone = "neutral", ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold",
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
