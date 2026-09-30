"use client";

import { createContext, useCallback, useContext, useEffect, useRef, useState, type ReactNode } from "react";
import { api, tokenStore } from "./api";
import type { HistoryItem, ResearchResult, User } from "./types";

/* ---------------- Toasts ---------------- */
type ToastKind = "success" | "error" | "info";
interface Toast { id: number; kind: ToastKind; text: string }
const ToastCtx = createContext<(kind: ToastKind, text: string) => void>(() => {});
export const useToast = () => useContext(ToastCtx);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const push = useCallback((kind: ToastKind, text: string) => {
    const id = Date.now() + Math.random();
    setToasts((t) => [...t, { id, kind, text }]);
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 4500);
  }, []);
  return (
    <ToastCtx.Provider value={push}>
      {children}
      <div className="toasts" role="status" aria-live="polite">
        {toasts.map((t) => <div key={t.id} className={`toast toast-${t.kind}`}>{t.text}</div>)}
      </div>
    </ToastCtx.Provider>
  );
}

/* ---------------- Auth ---------------- */
interface AuthValue {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}
const AuthCtx = createContext<AuthValue | null>(null);
export const useAuth = () => {
  const v = useContext(AuthCtx);
  if (!v) throw new Error("useAuth outside AuthProvider");
  return v;
};

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    if (!tokenStore.get()) { setLoading(false); return; }
    api.me()
      .then((u) => { if (!cancelled) setUser(u); })
      .catch(() => { tokenStore.clear(); })
      .finally(() => { if (!cancelled) setLoading(false); });
    const onUnauthorized = () => setUser(null);
    window.addEventListener("ra:unauthorized", onUnauthorized);
    return () => { cancelled = true; window.removeEventListener("ra:unauthorized", onUnauthorized); };
  }, []);

  const login = async (email: string, password: string) => {
    const r = await api.login(email, password);
    tokenStore.set(r.access_token); setUser(r.user);
  };
  const register = async (email: string, password: string) => {
    const r = await api.register(email, password);
    tokenStore.set(r.access_token); setUser(r.user);
  };
  const logout = async () => {
    await api.logout();
    tokenStore.clear(); setUser(null);
  };

  return <AuthCtx.Provider value={{ user, loading, login, register, logout }}>{children}</AuthCtx.Provider>;
}

/* ---------------- Research session (per signed-in app shell) ---------------- */
interface ResearchValue {
  running: boolean;
  elapsedMs: number;
  result: ResearchResult | null;
  error: string | null;
  run: (question: string, image?: File | null) => Promise<void>;
  reset: () => void;
  recent: HistoryItem[];
  recentHidden: boolean;
  hideRecent: () => void;
  refreshHistory: () => Promise<void>;
}
const ResearchCtx = createContext<ResearchValue | null>(null);
export const useResearch = () => {
  const v = useContext(ResearchCtx);
  if (!v) throw new Error("useResearch outside ResearchProvider");
  return v;
};

export function ResearchProvider({ children }: { children: ReactNode }) {
  const toast = useToast();
  const [running, setRunning] = useState(false);
  const [elapsedMs, setElapsedMs] = useState(0);
  const [result, setResult] = useState<ResearchResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [recent, setRecent] = useState<HistoryItem[]>([]);
  const [recentHidden, setRecentHidden] = useState(false);
  const timer = useRef<ReturnType<typeof setInterval> | null>(null);

  const refreshHistory = useCallback(async () => {
    try { setRecent((await api.history()).slice(0, 5)); } catch { /* sidebar is best-effort */ }
  }, []);

  useEffect(() => {
    setRecentHidden(window.localStorage.getItem("ra_hide_recent") === "1");
    void refreshHistory();
    return () => { if (timer.current) clearInterval(timer.current); };
  }, [refreshHistory]);

  const run = useCallback(async (question: string, image?: File | null) => {
    setRunning(true); setError(null); setResult(null); setElapsedMs(0);
    const t0 = Date.now();
    timer.current = setInterval(() => setElapsedMs(Date.now() - t0), 200);
    try {
      const r = await api.research(question, image);
      setResult({ ...r, finishedAt: new Date().toISOString(), durationMs: Date.now() - t0, usedImage: !!image });
      setRecentHidden(false); window.localStorage.removeItem("ra_hide_recent");
      void refreshHistory();
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Research request failed.";
      setError(msg); toast("error", msg);
    } finally {
      if (timer.current) clearInterval(timer.current);
      setRunning(false);
    }
  }, [refreshHistory, toast]);

  const reset = useCallback(() => { setResult(null); setError(null); }, []);
  const hideRecent = useCallback(() => {
    window.localStorage.setItem("ra_hide_recent", "1"); setRecentHidden(true);
  }, []);

  return (
    <ResearchCtx.Provider value={{ running, elapsedMs, result, error, run, reset, recent, recentHidden, hideRecent, refreshHistory }}>
      {children}
    </ResearchCtx.Provider>
  );
}
