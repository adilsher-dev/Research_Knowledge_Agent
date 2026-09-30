"use client";
import { useRef, useState } from "react";
import { Icon } from "./Icon";
import { api } from "@/lib/api";
import { validatePdf } from "@/lib/format";
import { useToast } from "@/lib/providers";

/** Uploads a PDF to the user's private knowledge base. */
export function FileUpload({ onUploaded, variant = "chip" }: { onUploaded?: () => void; variant?: "chip" | "drop" }) {
  const input = useRef<HTMLInputElement>(null);
  const toast = useToast();
  const [busy, setBusy] = useState(false);
  const [drag, setDrag] = useState(false);

  const handle = async (file: File | undefined) => {
    if (!file) return;
    const problem = validatePdf(file);
    if (problem) { toast("error", problem); return; }
    setBusy(true);
    try {
      const r = await api.uploadPdf(file);
      toast("success", `${r.filename} added (${r.chunk_count} chunks).`);
      onUploaded?.();
    } catch (e) {
      toast("error", e instanceof Error ? e.message : "PDF upload failed.");
    } finally {
      setBusy(false);
      if (input.current) input.current.value = "";
    }
  };

  const hidden = <input ref={input} type="file" accept="application/pdf" hidden onChange={(e) => handle(e.target.files?.[0])} />;

  if (variant === "drop") {
    return (
      <div className={`dropzone ${drag ? "drag" : ""}`}
        onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
        onDragLeave={() => setDrag(false)}
        onDrop={(e) => { e.preventDefault(); setDrag(false); void handle(e.dataTransfer.files?.[0]); }}>
        {hidden}
        <Icon name="upload" size={22} />
        <p>{busy ? "Uploading and indexing… large PDFs can take a while." : "Drag a PDF here, or"}</p>
        <button className="btn btn-primary" disabled={busy} onClick={() => input.current?.click()}>
          {busy ? "Processing…" : "Choose PDF"}
        </button>
      </div>
    );
  }
  return (
    <>
      {hidden}
      <button type="button" className="chip" disabled={busy} onClick={() => input.current?.click()}>
        <Icon name="upload" size={16} /> {busy ? "Uploading…" : "Upload PDF"}
      </button>
    </>
  );
}
