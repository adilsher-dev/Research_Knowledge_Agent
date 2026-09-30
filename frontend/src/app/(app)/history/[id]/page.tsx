"use client";
import { use, useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { AnswerPanel } from "@/components/AnswerPanel";
import { ErrorState, LoadingState } from "@/components/States";
import { api } from "@/lib/api";
import { fmtDate } from "@/lib/format";
import type { HistoryItem } from "@/lib/types";

export default function HistoryDetail({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [item, setItem] = useState<HistoryItem | null>(null);
  const [error, setError] = useState<string | null>(null);
  const load = useCallback(async () => {
    setError(null); setItem(null);
    try { setItem(await api.historyItem(Number(id))); } catch (e) { setError(e instanceof Error ? e.message : "Could not load this research record."); }
  }, [id]);
  useEffect(() => { void load(); }, [load]);

  return (
    <div className="page">
      <Link href="/history" className="link-btn">← Back to history</Link>
      {error ? <ErrorState message={error} onRetry={load} /> : !item ? <LoadingState /> : (
        <>
          <p className="muted">{fmtDate(item.created_at)}</p>
          <AnswerPanel question={item.question} answer={item.answer ?? ""} route={item.route} />
          <p className="foot-note">Saved runs keep the question, route and answer. Retrieved chunks and plan details are not stored.</p>
        </>
      )}
    </div>
  );
}
