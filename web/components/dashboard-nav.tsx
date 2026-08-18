"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { cn } from "@/lib/utils";
import { useAgentStream } from "@/lib/agent-stream-context";
import { useAuth } from "@/lib/auth-context";

const LINKS = [
  { href: "/dashboard", label: "Executive Overview" },
  { href: "/dashboard/playbooks", label: "Playbooks" },
  { href: "/dashboard/assets", label: "Asset Surface Map" },
  { href: "/dashboard/stream", label: "Agent Stream" },
];

export function DashboardNav() {
  const pathname = usePathname();
  const { connected } = useAgentStream();
  const { logout } = useAuth();

  return (
    <header className="border-b border-slate-200 dark:border-slate-800">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-3">
        <div className="flex items-center gap-6">
          <span className="text-sm font-semibold text-difesa-forest dark:text-difesa-cream">Difesa</span>
          <nav className="flex gap-1">
            {LINKS.map((link) => {
              const isActive = pathname === link.href;
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={cn(
                    "rounded-md px-3 py-1.5 text-sm font-medium transition-colors",
                    isActive
                      ? "bg-difesa-forest text-white dark:bg-difesa-cream dark:text-difesa-forest"
                      : "text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800"
                  )}
                >
                  {link.label}
                </Link>
              );
            })}
          </nav>
        </div>
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400">
            <span
              className={cn("h-2 w-2 rounded-full", connected ? "bg-difesa-leaf" : "bg-slate-400")}
              aria-hidden
            />
            {connected ? "Live" : "Disconnected"}
          </span>
          <button
            onClick={logout}
            className="text-xs text-slate-500 underline hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200"
          >
            Sign out
          </button>
        </div>
      </div>
    </header>
  );
}
