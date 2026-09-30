import { Icon } from "./Icon";
import { buildStages } from "@/lib/routes";
import { fmtSeconds } from "@/lib/format";
import type { ResearchResult } from "@/lib/types";

interface Props { running: boolean; elapsedMs: number; result: ResearchResult | null; error: string | null; live?: boolean }

export function ResearchActivity({ running, elapsedMs, result, error, live }: Props) {
  return (
    <section className="panel activity" aria-label="Research Agent Activity">
      <header className="panel-head">
        <h2><Icon name="bot" size={18} /> Research Agent Activity</h2>
      </header>
      <p className="panel-sub">{live ? "Live workflow of your research agent" : "Steps of the most recent research run"}</p>

      {running && (
        <div className="running">
          <span className="spinner" />
          <div>
            <strong>Research in progress · {fmtSeconds(elapsedMs)}</strong>
            <p>The backend runs the whole workflow in one request and reports the steps when it finishes, so
              per-step progress can’t be shown live.</p>
          </div>
        </div>
      )}

      {!running && error && <div className="notice notice-error" role="alert">{error}</div>}

      {!running && !error && !result && <p className="muted pad">No research run yet. Ask a question to see what the agent did.</p>}

      {!running && result && (
        <>
          <ol className="stages">
            {buildStages(result).map((s, i) => (
              <li key={i} className={`stage stage-${s.status}`}>
                <span className="stage-dot">{s.status === "done" ? <Icon name="check" size={14} /> : s.status === "warn" ? "!" : "–"}</span>
                <div>
                  <strong>{s.title}</strong>
                  <p>{s.detail}</p>
                </div>
                <span className={`badge badge-${s.status}`}>{s.status === "done" ? "Completed" : s.status === "warn" ? "Check" : "Skipped"}</span>
              </li>
            ))}
          </ol>
          <p className="foot-note">Total time {fmtSeconds(result.durationMs)} (measured in your browser). Steps are derived from the finished response.</p>
        </>
      )}
    </section>
  );
}
