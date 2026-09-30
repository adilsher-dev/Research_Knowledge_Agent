import { routeLabel } from "@/lib/routes";
export function RouteBadge({ route }: { route: string | null | undefined }) {
  return <span className="badge badge-route">{routeLabel(route)}</span>;
}
