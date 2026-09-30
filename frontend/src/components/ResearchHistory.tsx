import Link from "next/link";
import { RouteBadge } from "./RouteBadge";
import { fmtDate, preview } from "@/lib/format";
import type { HistoryItem } from "@/lib/types";

export function ResearchHistory({ items }: { items: HistoryItem[] }) {
  return (
    <ul className="history-list">
      {items.map((h) => (
        <li key={h.id}>
          <Link href={`/history/${h.id}`}>
            <div className="history-top"><strong>{h.question}</strong><RouteBadge route={h.route} /></div>
            <p>{preview(h.answer, 180)}</p>
            <span className="muted">{fmtDate(h.created_at)}</span>
          </Link>
        </li>
      ))}
    </ul>
  );
}
