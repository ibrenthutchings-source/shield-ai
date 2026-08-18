"use client";

import { createContext, useContext, useEffect, useRef, useState, type ReactNode } from "react";

import { useAuth } from "@/lib/auth-context";
import type { AgentStreamMessage } from "@/lib/types";

const WS_URL = process.env.NEXT_PUBLIC_WS_URL ?? "ws://localhost:8000";
const MAX_MESSAGES = 200;

interface AgentStreamContextValue {
  messages: AgentStreamMessage[];
  connected: boolean;
  clear: () => void;
}

const AgentStreamContext = createContext<AgentStreamContextValue | undefined>(undefined);

export function AgentStreamProvider({ children }: { children: ReactNode }) {
  const { token } = useAuth();
  const [messages, setMessages] = useState<AgentStreamMessage[]>([]);
  const [connected, setConnected] = useState(false);
  const socketRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!token) {
      setConnected(false);
      return;
    }

    const socket = new WebSocket(`${WS_URL}/ws/agent-stream?token=${encodeURIComponent(token)}`);
    socketRef.current = socket;

    socket.onopen = () => setConnected(true);
    socket.onclose = () => setConnected(false);
    socket.onerror = () => setConnected(false);
    socket.onmessage = (event) => {
      try {
        const parsed = JSON.parse(event.data) as AgentStreamMessage;
        setMessages((prev) => [...prev.slice(-MAX_MESSAGES + 1), parsed]);
      } catch {
        // Ignore non-JSON frames.
      }
    };

    return () => socket.close();
  }, [token]);

  function clear() {
    setMessages([]);
  }

  return (
    <AgentStreamContext.Provider value={{ messages, connected, clear }}>
      {children}
    </AgentStreamContext.Provider>
  );
}

export function useAgentStream(): AgentStreamContextValue {
  const ctx = useContext(AgentStreamContext);
  if (!ctx) throw new Error("useAgentStream must be used within an AgentStreamProvider");
  return ctx;
}
