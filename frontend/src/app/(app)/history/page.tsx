"use client";
import { useCallback, useEffect, useState } from "react";
import { EmptyState, ErrorState, LoadingState } from "@/components/States";
import { ResearchHistory } from "@/components/ResearchHistory";
import { api } from "@/lib/api";
import type { HistoryItem } from "@/lib/types";

export default function HistoryPage() {
  const [items, setItems] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const load = useCallback(async () => {
    setLoading(true); setError(null);
    try { setItems(await api.history()); } catch (e) { setError(e instanceof Error ? e.message : "Could not load history."); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => { void load(); }, [load]);
  return (
    <div className="page">
      <h1>History</h1>
      <p className="muted">Your previous research runs. Only you can see these.</p>
      <div className="panel">
        {loading ? <LoadingState /> : error ? <ErrorState message={error} onRetry={load} />
          : items.length === 0 ? <EmptyState icon="clock" title="No research yet">Completed research runs are saved here.</EmptyState>
          : <ResearchHistory items={items} />}
      </div>
    </div>
  );
}
