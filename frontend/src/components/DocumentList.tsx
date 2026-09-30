"use client";
import { useState } from "react";
import { Icon } from "./Icon";
import { fmtDate } from "@/lib/format";
import type { DocumentItem } from "@/lib/types";

export function DocumentList({ docs, onDelete }: { docs: DocumentItem[]; onDelete: (d: DocumentItem) => Promise<void> }) {
  const [busy, setBusy] = useState<number | null>(null);
  const [confirm, setConfirm] = useState<number | null>(null);

  const del = async (d: DocumentItem) => {
    setBusy(d.id);
    try { await onDelete(d); } finally { setBusy(null); setConfirm(null); }
  };

  return (
    <div className="table-wrap">
      <table className="table">
        <thead><tr><th>Filename</th><th>Uploaded</th><th>Type</th><th>Status</th><th>Chunks</th><th /></tr></thead>
        <tbody>
          {docs.map((d) => (
            <tr key={d.id}>
              <td data-label="Filename"><Icon name="file" size={16} /> {d.filename}</td>
              <td data-label="Uploaded">{fmtDate(d.upload_date)}</td>
              <td data-label="Type">{d.content_type === "application/pdf" ? "PDF" : d.content_type ?? "—"}</td>
              <td data-label="Status"><span className={`badge ${d.status === "ready" ? "badge-done" : "badge-warn"}`}>{d.status}</span></td>
              <td data-label="Chunks">{d.chunk_count}</td>
              <td className="actions">
                {confirm === d.id ? (
                  <>
                    <button className="btn btn-danger" disabled={busy === d.id} onClick={() => del(d)}>{busy === d.id ? "Deleting…" : "Confirm delete"}</button>
                    <button className="btn btn-ghost" onClick={() => setConfirm(null)} disabled={busy === d.id}>Cancel</button>
                  </>
                ) : (
                  <button className="icon-btn" aria-label={`Delete ${d.filename}`} onClick={() => setConfirm(d.id)}><Icon name="trash" size={16} /></button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
