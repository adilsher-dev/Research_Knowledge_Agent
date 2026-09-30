import type { Metadata } from "next";
import type { ReactNode } from "react";
import "./globals.css";
import { AuthProvider, ToastProvider } from "@/lib/providers";

export const metadata: Metadata = {
  title: "AI Research Agent",
  description: "Research with your private documents and the web — RAG, LangGraph, multimodal.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" data-theme="dark">
      <body>
        <ToastProvider><AuthProvider>{children}</AuthProvider></ToastProvider>
      </body>
    </html>
  );
}
