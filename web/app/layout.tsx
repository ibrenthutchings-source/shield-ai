import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ShieldAI",
  description: "Agentic cybersecurity and threat monitoring for SMBs, schools, and non-profits",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
