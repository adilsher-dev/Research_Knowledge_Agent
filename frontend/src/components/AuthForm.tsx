"use client";
import { useEffect, useState, type FormEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Icon } from "./Icon";
import { useAuth, useToast } from "@/lib/providers";

export function AuthForm({ mode }: { mode: "login" | "register" }) {
  const { user, login, register } = useAuth();
  const router = useRouter();
  const toast = useToast();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const isLogin = mode === "login";

  useEffect(() => { if (user) router.replace("/home"); }, [user, router]);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    if (!isLogin && password.length < 8) { setError("Password must be at least 8 characters."); return; }
    setBusy(true);
    try {
      await (isLogin ? login : register)(email.trim(), password);
      toast("success", isLogin ? "Signed in." : "Account created.");
      router.replace("/home");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally { setBusy(false); }
  };

  return (
    <div className="auth-page">
      <form className="auth-card" onSubmit={submit}>
        <div className="brand"><span className="brand-icon dark"><Icon name="book" size={26} /></span>
          <div><div className="brand-name dark">Research Agent</div><div className="brand-sub dark">AI Powered • RAG • LangGraph</div></div></div>
        <h1>{isLogin ? "Welcome back" : "Create your account"}</h1>
        <label>Email<input type="email" required autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} /></label>
        <label>Password
          <input type="password" required minLength={isLogin ? undefined : 8} maxLength={72}
            autoComplete={isLogin ? "current-password" : "new-password"} value={password} onChange={(e) => setPassword(e.target.value)} />
        </label>
        {!isLogin && <p className="hint">At least 8 characters.</p>}
        {error && <div className="notice notice-error" role="alert">{error}</div>}
        <button className="btn btn-primary btn-block" disabled={busy}>{busy ? "Please wait…" : isLogin ? "Sign in" : "Create account"}</button>
        <p className="hint center">
          {isLogin ? <>No account? <Link href="/register">Create one</Link></> : <>Already registered? <Link href="/login">Sign in</Link></>}
        </p>
      </form>
    </div>
  );
}
