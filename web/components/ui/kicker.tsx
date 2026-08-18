import type { HTMLAttributes } from "react";

import { cn } from "@/lib/utils";

/** Small uppercase, letter-spaced label above a page heading — cue from dendrai-dashboard's header kicker. */
export function Kicker({ className, children, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "mb-1 text-[10px] font-bold uppercase tracking-[0.2em] text-difesa-forest dark:text-difesa-leaf",
        className
      )}
      {...props}
    >
      ▸ {children}
    </div>
  );
}
