import type { DocSource } from "@/lib/types";

export function ChunkCard({ index, chunk, full }: { index: number; chunk: DocSource; full?: boolean }) {
  return (
    <div className="chunk">
      <div className="chunk-head">
        <strong>Chunk {index + 1}</strong>
        <span className="muted">{chunk.filename ?? "Unknown file"}{chunk.chunk_index != null && ` · #${chunk.chunk_index}`}</span>
      </div>
      <p className={full ? "" : "clamp"}>{chunk.content_preview}</p>
      <div className="chunk-tags">
        {chunk.similarity != null && <span className="tag">similarity {chunk.similarity.toFixed(3)}</span>}
        {chunk.matched_by?.map((m) => <span key={m} className="tag">{m}</span>)}
      </div>
    </div>
  );
}
