"use client";
import { useState } from "react";
import { Icon } from "@/components/Icon";
import { EmptyState, ErrorState, LoadingState } from "@/components/States";
import { useDocuments } from "@/components/useDocuments";
import { fmtDate } from "@/lib/format";
import Link from "next/link";

export default function KnowledgeBasePage() {
  const { docs, loading, error, reload } = useDocuments();
  const [q, setQ] = useState("");
  const list = docs.filter((d) => d.filename.toLowerCase().includes(q.toLowerCase()));
  const totalChunks = docs.reduce((n, d) => n + d.chunk_count, 0);

  return (
    <div className="page">
      <h1>Knowledge Base</h1>
      <p className="muted">These documents are your private knowledge. When a question is routed to “document”, the agent searches only the chunks of
        these files (hybrid semantic + full-text search, merged with RRF). Nobody else can retrieve them.</p>
      {!loading && !error && (
        <div className="stat-row">
          <div className="panel stat"><strong>{docs.length}</strong><span className="muted">documents</span></div>
          <div className="panel stat"><strong>{totalChunks}</strong><span className="muted">chunks indexed</span></div>
        </div>
      )}
      <div className="panel">
        <label className="search"><Icon name="search" size={16} />
          <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Filter by filename" aria-label="Filter documents by filename" />
        </label>
        <p className="foot-note">Search is by filename. Chunk text is searched by the agent when you run a research query.</p>
        {loading ? <LoadingState /> : error ? <ErrorState message={error} onRetry={reload} />
          : list.length === 0 ? <EmptyState icon="db" title={docs.length ? "No matching documents" : "Your knowledge base is empty"}>
              {docs.length ? "Try a different filename." : <>Add PDFs on the <Link href="/documents">Documents</Link> page.</>}</EmptyState>
          : <ul className="kb-list">{list.map((d) => (
              <li key={d.id}><Icon name="file" /><div><strong>{d.filename}</strong>
                <span className="muted">{d.chunk_count} chunks · {d.status} · added {fmtDate(d.upload_date)}</span></div></li>))}</ul>}
      </div>
    </div>
  );
}
