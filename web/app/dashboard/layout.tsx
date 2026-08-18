"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

import { AgentStreamProvider } from "@/lib/agent-stream-context";
import { useAuth } from "@/lib/auth-context";
import { DashboardNav } from "@/components/dashboard-nav";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { token, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !token) router.replace("/login");
  }, [isLoading, token, router]);

  if (isLoading || !token) return null;

  return (
    <AgentStreamProvider>
      <div className="min-h-screen">
        <DashboardNav />
        <div className="mx-auto max-w-6xl p-4">{children}</div>
      </div>
    </AgentStreamProvider>
  );
}
