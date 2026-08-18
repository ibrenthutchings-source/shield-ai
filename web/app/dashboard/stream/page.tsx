"use client";

import { useEffect, useRef } from "react";

import { useAgentStream } from "@/lib/agent-stream-context";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function AgentStreamPage() {
  const { messages, connected, clear } = useAgentStream();
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight });
  }, [messages]);

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">Real-Time Agent Stream</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Live status updates from Difesa's agents as they run.
          </p>
        </div>
        <Button variant="outline" onClick={clear}>
          Clear
        </Button>
      </div>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Console</CardTitle>
          <Badge tone={connected ? "success" : "neutral"}>{connected ? "connected" : "disconnected"}</Badge>
        </CardHeader>
        <CardContent>
          <div
            ref={scrollRef}
            className="h-96 overflow-y-auto rounded-md bg-slate-950 p-3 font-mono text-xs text-slate-100"
          >
            {messages.length === 0 ? (
              <p className="text-slate-500">Waiting for agent activity…</p>
            ) : (
              messages.map((message, index) => (
                <div key={index} className="mb-1 flex gap-2">
                  <span className="text-slate-500">[{message.agent}]</span>
                  <span
                    className={
                      message.status === "error"
                        ? "text-red-400"
                        : message.status === "completed"
                          ? "text-emerald-400"
                          : "text-slate-100"
                    }
                  >
                    {JSON.stringify(message)}
                  </span>
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
