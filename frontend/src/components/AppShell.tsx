"use client";
import { useEffect, useState, type ReactNode } from "react";
import { useRouter } from "next/navigation";
import { AppHeader } from "./AppHeader";
import { Sidebar } from "./Sidebar";
import { LoadingState } from "./States";
import { ResearchProvider, useAuth } from "@/lib/providers";

export function AppShell({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [menu, setMenu] = useState(false);

  useEffect(() => { if (!loading && !user) router.replace("/login"); }, [loading, user, router]);

  if (loading || !user) return <div className="fullscreen"><LoadingState label="Checking your session…" /></div>;

  return (
    <ResearchProvider>
      <div className="shell">
        <AppHeader onMenu={() => setMenu(true)} />
        <div className="shell-body">
          <Sidebar open={menu} onClose={() => setMenu(false)} />
          <main className="main">{children}</main>
        </div>
      </div>
    </ResearchProvider>
  );
}
