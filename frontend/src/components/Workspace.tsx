"use client";
import { ResearchComposer } from "./ResearchComposer";
import { ResearchActivity } from "./ResearchActivity";
import { AnswerPanel } from "./AnswerPanel";
import { SourcePanel } from "./SourcePanel";
import { useResearch } from "@/lib/providers";

/** The 3-column research workspace from the reference design. */
export function Workspace({ hero }: { hero?: boolean }) {
  const { running, elapsedMs, result, error } = useResearch();
  return (
    <div className="workspace">
      <div className="ws-center">
        <ResearchComposer hero={hero} />
        <div className="ws-grid">
          <ResearchActivity running={running} elapsedMs={elapsedMs} result={result} error={error} live />
          {result ? (
            <AnswerPanel question={result.question} answer={result.answer} route={result.route}
              planReason={result.plan_reason} detail={result} />
          ) : (
            <section className="panel output">
              <header className="panel-head"><h2>Research Output</h2>
                {running && <span className="badge badge-warn">In Progress</span>}</header>
              <p className="muted pad">{running ? "Waiting for the agent to finish…" : "Your answer, route and plan will appear here."}</p>
            </section>
          )}
        </div>
      </div>
      <SourcePanel sources={result?.document_sources ?? []} hasWeb={result?.has_web_result} />
    </div>
  );
}
