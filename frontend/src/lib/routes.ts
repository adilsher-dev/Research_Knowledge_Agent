import type { ResearchResult } from "./types";

export const ROUTE_LABELS: Record<string, string> = {
  direct: "Direct answer",
  document: "Documents",
  web: "Web",
  both: "Documents + Web",
  image: "Image",
  image_document: "Image + Documents",
  image_web: "Image + Web",
  image_both: "Image + Documents + Web",
};

export const routeLabel = (r: string | null | undefined) =>
  r ? ROUTE_LABELS[r] ?? r : "Unknown";

export const routeUses = (route: string | null | undefined) => ({
  image: !!route && route.startsWith("image"),
  document: !!route && (route.includes("document") || route.endsWith("both")),
  web: !!route && (route.includes("web") || route.endsWith("both")),
});

export type StageStatus = "done" | "skipped" | "warn";
export interface Stage { title: string; detail: string; status: StageStatus }

/**
 * The backend does not stream progress. These stages are derived from the
 * *completed* response (route + returned data) and describe what actually ran.
 */
export function buildStages(r: ResearchResult): Stage[] {
  const u = routeUses(r.route);
  const n = r.document_sources.length;
  const stages: Stage[] = [
    { title: "Planning", status: "done", detail: `Planner chose route “${routeLabel(r.route)}”.` },
  ];
  if (u.image) {
    stages.push({
      title: "Analysing image",
      status: r.has_image_result ? "done" : "warn",
      detail: r.has_image_result ? "Vision model returned an analysis." : "Route included an image but no analysis was returned.",
    });
  }
  stages.push(
    u.document
      ? { title: "Searching knowledge base", status: "done",
          detail: `${n} chunk${n === 1 ? "" : "s"} retrieved (hybrid search + RRF).` }
      : { title: "Searching knowledge base", status: "skipped", detail: "Not used for this route." },
  );
  stages.push(
    u.web
      ? { title: "Searching web", status: r.has_web_result ? "done" : "warn",
          detail: r.has_web_result ? "Web research returned a result." : "Route included web research but no web result was returned." }
      : { title: "Searching web", status: "skipped", detail: "Not used for this route." },
  );
  stages.push(
    { title: "Synthesizing answer", status: r.answer ? "done" : "warn", detail: r.answer ? "Final answer generated." : "No answer text returned." },
    { title: "Saved to history", status: "done", detail: "The backend stored this run in your research history." },
  );
  return stages;
}
