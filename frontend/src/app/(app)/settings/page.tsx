"use client";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { fmtDate } from "@/lib/format";
import { useAuth, useResearch } from "@/lib/providers";

export default function SettingsPage() {
  const { user, logout } = useAuth();
  const { hideRecent } = useResearch();
  const router = useRouter();
  return (
    <div className="page">
      <h1>Settings</h1>
      <div className="panel">
        <h2>Account</h2>
        <dl className="kv"><dt>Email</dt><dd>{user?.email}</dd><dt>Member since</dt><dd>{user ? fmtDate(user.created_at) : "—"}</dd></dl>
        <button className="btn btn-ghost" onClick={async () => { await logout(); router.replace("/login"); }}>Sign out</button>
      </div>
      <div className="panel">
        <h2>Preferences</h2>
        <p className="muted">Use the sun/moon button in the header to switch theme. It is remembered on this device.</p>
        <button className="btn btn-ghost" onClick={hideRecent}>Hide “Recent Searches” in sidebar</button>
      </div>
      <div className="panel">
        <h2>Connection</h2>
        <dl className="kv"><dt>Backend URL</dt><dd>{api.baseUrl}</dd></dl>
      </div>
    </div>
  );
}
