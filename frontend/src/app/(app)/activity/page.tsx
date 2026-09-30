"use client";
import { useEffect, useMemo, useState } from "react";
import { ResearchActivity } from "@/components/ResearchActivity";
import { ChunkCard } from "@/components/ChunkCard";
import { EmptyState } from "@/components/States";
import { RouteBadge } from "@/components/RouteBadge";
import { api } from "@/lib/api";
import { routeLabel } from "@/lib/routes";
import { useResearch } from "@/lib/providers";
import type { HistoryItem } from "@/lib/types";

export default function ActivityPage() {
  const { running, elapsedMs, result, error } = useResearch();
  const [history, setHistory] = useState<HistoryItem[]>([]);
  useEffect(() => { api.history().then(setHistory).catch(() => {}); }, [result]);
  const counts = useMemo(() => {
    const m: Record<string, number> = {};
    history.forEach((h) => { const k = h.route ?? "unknown"; m[k] = (m[k] ?? 0) + 1; });
    return Object.entries(m).sort((a, b) => b[1] - a[1]);
  }, [history]);

  return (
    <div className="page">
      <h1>Agent Activity</h1>
      <p className="muted">What the agent did on your latest run in this browser session, plus how your saved runs were routed.</p>
      <ResearchActivity running={running} elapsedMs={elapsedMs} result={result} error={error} />
      {result && (
        <div className="panel">
          <header className="panel-head"><h2>Technical details</h2><RouteBadge route={result.route} /></header>
          <details className="expander" open><summary>Plan / reason</summary><p>{result.plan_reason || "—"}</p></details>
          <details className="expander"><summary>Retrieved chunks ({result.document_sources.length})</summary>
            <div className="chunk-list">{result.document_sources.map((c, i) => <ChunkCard key={i} index={i} chunk={c} full />)}</div></details>
          <details className="expander"><summary>Flags</summary>
            <p>Image analysis returned: {String(result.has_image_result)} · Web result returned: {String(result.has_web_result)}</p></details>
        </div>
      )}
      <div className="panel">
        <header className="panel-head"><h2>Routes used in your history</h2></header>
        {counts.length === 0 ? <EmptyState icon="bot" title="No saved runs yet" /> : (
          <ul className="route-counts">{counts.map(([r, n]) => <li key={r}><span>{routeLabel(r)}</span><strong>{n}</strong></li>)}</ul>
        )}
      </div>
    </div>
  );
}
