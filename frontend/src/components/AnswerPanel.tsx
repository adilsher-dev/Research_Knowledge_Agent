import { Icon } from "./Icon";
import { RouteBadge } from "./RouteBadge";
import { routeUses } from "@/lib/routes";
import type { ResearchResponse } from "@/lib/types";

/** Renders answer text: paragraphs, "-"/"*" bullets and **bold**. No HTML injection. */
function Rich({ text }: { text: string }) {
  const blocks = text.split(/\n{2,}/);
  const inline = (s: string) =>
    s.split(/(\*\*[^*]+\*\*)/g).map((p, i) =>
      p.startsWith("**") && p.endsWith("**") ? <strong key={i}>{p.slice(2, -2)}</strong> : <span key={i}>{p}</span>);
  return (
    <>
      {blocks.map((b, i) => {
        const lines = b.split("\n");
        if (lines.every((l) => /^\s*[-*•]\s+/.test(l)))
          return <ul key={i}>{lines.map((l, j) => <li key={j}>{inline(l.replace(/^\s*[-*•]\s+/, ""))}</li>)}</ul>;
        return <p key={i}>{lines.map((l, j) => <span key={j}>{inline(l)}{j < lines.length - 1 && <br />}</span>)}</p>;
      })}
    </>
  );
}

interface Props {
  question: string;
  answer: string;
  route: string | null;
  planReason?: string;
  status?: "running" | "complete";
  detail?: Pick<ResearchResponse, "document_sources" | "has_web_result" | "has_image_result">;
}

export function AnswerPanel({ question, answer, route, planReason, status = "complete", detail }: Props) {
  const u = routeUses(route);
  return (
    <section className="panel output" aria-label="Research Output">
      <header className="panel-head">
        <h2><Icon name="file" size={18} /> Research Output</h2>
        <span className={`badge ${status === "running" ? "badge-warn" : "badge-done"}`}>{status === "running" ? "In Progress" : "Complete"}</span>
      </header>
      <div className="answer-card">
        <div className="answer-meta"><RouteBadge route={route} /></div>
        <h3>{question}</h3>
        <div className="answer-body"><Rich text={answer || "No answer text was returned."} /></div>
        {detail && (
          <div className="used">
            <Icon name="spark" size={16} />
            <span>Used: {[
              u.image && detail.has_image_result && "image analysis",
              u.document && `${detail.document_sources.length} document chunk${detail.document_sources.length === 1 ? "" : "s"}`,
              u.web && detail.has_web_result && "web research",
            ].filter(Boolean).join(", ") || "model knowledge only (no documents or web)"}</span>
          </div>
        )}
      </div>
      {planReason && (
        <details className="expander">
          <summary>Plan / reason for route</summary>
          <p>{planReason}</p>
        </details>
      )}
      {detail && u.web && (
        <p className="foot-note">Web research was used, but this API does not return a list of web URLs, so no web citations are shown.</p>
      )}
    </section>
  );
}
