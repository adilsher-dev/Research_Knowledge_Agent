import type { ReactNode } from "react";
import { Icon, type IconName } from "./Icon";

export function EmptyState({ icon = "leaf", title, children }: { icon?: IconName; title: string; children?: ReactNode }) {
  return (
    <div className="state">
      <div className="state-icon"><Icon name={icon} size={22} /></div>
      <strong>{title}</strong>
      {children && <p>{children}</p>}
    </div>
  );
}

export function LoadingState({ label = "Loading…" }: { label?: string }) {
  return <div className="state" role="status"><span className="spinner" /><p>{label}</p></div>;
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="state state-error" role="alert">
      <div className="state-icon"><Icon name="alert" size={22} /></div>
      <strong>{message}</strong>
      {onRetry && <button className="btn btn-ghost" onClick={onRetry}>Try again</button>}
    </div>
  );
}
