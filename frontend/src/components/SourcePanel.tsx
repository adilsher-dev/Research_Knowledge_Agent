"use client";
import { useState } from "react";
import { Icon } from "./Icon";
import { ChunkCard } from "./ChunkCard";
import { EmptyState } from "./States";
import type { DocSource } from "@/lib/types";

/** Right-hand column: distinct document sources (from retrieved chunks) + the chunks themselves. */
export function SourcePanel({ sources, hasWeb }: { sources: DocSource[]; hasWeb?: boolean }) {
  const [all, setAll] = useState(false);
  const files = Array.from(
    sources.reduce((m, s) => {
      const k = s.filename ?? "Unknown file";
      const cur = m.get(k) ?? { name: k, chunks: 0, best: null as number | null };
      cur.chunks += 1;
      if (s.similarity != null && (cur.best == null || s.similarity > cur.best)) cur.best = s.similarity;
      return m.set(k, cur);
    }, new Map<string, { name: string; chunks: number; best: number | null }>()).values(),
  );
  const shown = all ? sources : sources.slice(0, 3);

  return (
    <div className="right-col">
      <section className="panel">
        <header className="panel-head"><h2><Icon name="db" size={18} /> Sources</h2><span className="count">{files.length}</span></header>
        {files.length === 0 ? (
          <EmptyState title="No document sources">Sources appear here when the agent retrieves from your PDFs.</EmptyState>
        ) : (
          <ul className="source-list">
            {files.map((f) => (
              <li key={f.name}>
                <span className="src-icon pdf">PDF</span>
                <div><strong>{f.name}</strong>
                  <span className="muted">{f.chunks} chunk{f.chunks === 1 ? "" : "s"}{f.best != null && ` · best similarity ${f.best.toFixed(3)}`}</span></div>
              </li>
            ))}
          </ul>
        )}
        {hasWeb && <p className="foot-note">Web research was used; the API does not return individual web sources.</p>}
      </section>

      <section className="panel">
        <header className="panel-head"><h2><Icon name="file" size={18} /> Retrieved Chunks</h2><span className="count">{sources.length}</span></header>
        {sources.length === 0 ? (
          <EmptyState title="No chunks retrieved" />
        ) : (
          <>
            <div className="chunk-list">{shown.map((c, i) => <ChunkCard key={i} index={i} chunk={c} />)}</div>
            {sources.length > 3 && (
              <button className="link-btn" onClick={() => setAll((a) => !a)}>{all ? "Show fewer" : "View all chunks"} <Icon name="chevron" size={14} /></button>
            )}
          </>
        )}
      </section>
    </div>
  );
}
