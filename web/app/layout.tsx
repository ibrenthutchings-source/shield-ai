import type { Metadata } from "next";
import "./globals.css";

import { AuthProvider } from "@/lib/auth-context";

export const metadata: Metadata = {
  title: "Difesa",
  description: "Agentic cybersecurity and threat monitoring for SMBs, schools, and non-profits",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-difesa-cream text-slate-900 dark:bg-slate-950 dark:text-slate-100">
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
