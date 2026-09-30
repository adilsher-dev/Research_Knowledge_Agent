"use client";
import { useState } from "react";
import { Icon } from "./Icon";
import { FileUpload } from "./FileUpload";
import { ImageUpload } from "./ImageUpload";
import { useResearch } from "@/lib/providers";

export function ResearchComposer({ hero }: { hero?: boolean }) {
  const { run, running, reset, result, error } = useResearch();
  const [question, setQuestion] = useState("");
  const [image, setImage] = useState<File | null>(null);

  const submit = async () => {
    const q = question.trim();
    if (!q || running) return;
    await run(q, image);
  };
  const clear = () => { setQuestion(""); setImage(null); reset(); };

  return (
    <div className={hero ? "hero" : "hero hero-compact"}>
      {hero && (
        <div className="hero-copy">
          <h1><Icon name="leaf" size={26} /> Welcome to AI Research Agent</h1>
          <p>Ask a question, upload a document, or share an image. The agent plans a route, searches your private
            knowledge base and/or the web, and writes an answer based on what it actually found.</p>
        </div>
      )}
      <div className="composer">
        <textarea value={question} rows={2} disabled={running} placeholder="What do you want to research today?"
          aria-label="Research question"
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) void submit(); }} />
        <div className="composer-bar">
          <FileUpload />
          <ImageUpload file={image} onChange={setImage} disabled={running} />
          <div className="spacer" />
          {(question || image || result || error) && (
            <button type="button" className="btn btn-ghost" onClick={clear} disabled={running}>Clear</button>
          )}
          <button type="button" className="btn btn-primary" onClick={submit} disabled={running || !question.trim()}>
            {running ? "Researching…" : <>Start Research <Icon name="arrow" size={16} /></>}
          </button>
        </div>
      </div>
    </div>
  );
}
