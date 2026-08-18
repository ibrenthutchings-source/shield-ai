"use client";

import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

import { login as apiLogin, register as apiRegister } from "@/lib/api";

const STORAGE_KEY = "shieldai_token";

interface AuthContextValue {
  token: string | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, orgName: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    setToken(localStorage.getItem(STORAGE_KEY));
    setIsLoading(false);
  }, []);

  async function login(email: string, password: string) {
    const { access_token } = await apiLogin(email, password);
    localStorage.setItem(STORAGE_KEY, access_token);
    setToken(access_token);
  }

  async function register(email: string, password: string, orgName: string) {
    await apiRegister(email, password, orgName);
    await login(email, password);
  }

  function logout() {
    localStorage.removeItem(STORAGE_KEY);
    setToken(null);
  }

  return (
    <AuthContext.Provider value={{ token, isLoading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
  return ctx;
}
