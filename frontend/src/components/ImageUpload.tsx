"use client";
import { useEffect, useRef, useState } from "react";
import { Icon } from "./Icon";
import { validateImage } from "@/lib/format";
import { useToast } from "@/lib/providers";

export function ImageUpload({ file, onChange, disabled }: { file: File | null; onChange: (f: File | null) => void; disabled?: boolean }) {
  const input = useRef<HTMLInputElement>(null);
  const toast = useToast();
  const [url, setUrl] = useState<string | null>(null);

  useEffect(() => {
    if (!file) { setUrl(null); return; }
    const u = URL.createObjectURL(file);
    setUrl(u);
    return () => URL.revokeObjectURL(u);
  }, [file]);

  const pick = (f: File | undefined) => {
    if (!f) return;
    const problem = validateImage(f);
    if (problem) { toast("error", problem); return; }
    onChange(f);
  };

  return (
    <>
      <input ref={input} type="file" accept="image/jpeg,image/png,image/webp,image/gif" hidden
        onChange={(e) => { pick(e.target.files?.[0]); e.target.value = ""; }} />
      {file && url ? (
        <span className="img-preview">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={url} alt="Selected upload preview" />
          <span>{file.name.length > 18 ? `${file.name.slice(0, 15)}…` : file.name}</span>
          <button type="button" onClick={() => onChange(null)} aria-label="Remove image" disabled={disabled}><Icon name="x" size={14} /></button>
        </span>
      ) : (
        <button type="button" className="chip" disabled={disabled} onClick={() => input.current?.click()}>
          <Icon name="image" size={16} /> Add Image
        </button>
      )}
    </>
  );
}
