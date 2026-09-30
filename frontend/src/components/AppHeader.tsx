"use client";
import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Icon } from "./Icon";
import { useAuth } from "@/lib/providers";

export function AppHeader({ onMenu }: { onMenu: () => void }) {
  const { user, logout } = useAuth();
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [theme, setTheme] = useState<"dark" | "light">("dark");
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const saved = window.localStorage.getItem("ra_theme");
    if (saved === "light" || saved === "dark") { setTheme(saved); document.documentElement.dataset.theme = saved; }
    const close = (e: MouseEvent) => { if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false); };
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, []);

  const toggleTheme = () => {
    const next = theme === "dark" ? "light" : "dark";
    setTheme(next); document.documentElement.dataset.theme = next;
    window.localStorage.setItem("ra_theme", next);
  };
  const signOut = async () => { await logout(); router.replace("/login"); };
  const initials = (user?.email ?? "?").slice(0, 2).toUpperCase();

  return (
    <header className="app-header">
      <button className="icon-btn menu-btn" onClick={onMenu} aria-label="Open navigation"><Icon name="menu" /></button>
      <div className="brand">
        <span className="brand-icon"><Icon name="book" size={26} /></span>
        <div>
          <div className="brand-name">Research Agent</div>
          <div className="brand-sub">AI Powered • RAG • LangGraph</div>
        </div>
      </div>
      <div className="header-right">
        <button className="icon-btn" onClick={toggleTheme} aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} theme`}>
          <Icon name={theme === "dark" ? "sun" : "moon"} />
        </button>
        <div className="profile" ref={ref}>
          <button className="profile-btn" onClick={() => setOpen((o) => !o)} aria-expanded={open}>
            <span className="avatar">{initials}</span>
            <span className="profile-email">{user?.email}</span>
            <Icon name="down" size={14} />
          </button>
          {open && (
            <div className="dropdown" role="menu">
              <div className="dropdown-email">{user?.email}</div>
              <button role="menuitem" onClick={() => { setOpen(false); router.push("/settings"); }}><Icon name="gear" size={16} /> Settings</button>
              <button role="menuitem" onClick={signOut}><Icon name="logout" size={16} /> Sign out</button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
