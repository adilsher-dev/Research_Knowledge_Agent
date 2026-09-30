"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Icon, type IconName } from "./Icon";
import { useResearch } from "@/lib/providers";
import { preview } from "@/lib/format";

const NAV: { href: string; label: string; icon: IconName }[] = [
  { href: "/home", label: "Home", icon: "home" },
  { href: "/research", label: "Research", icon: "search" },
  { href: "/knowledge-base", label: "Knowledge Base", icon: "db" },
  { href: "/documents", label: "Documents", icon: "file" },
  { href: "/activity", label: "Agent Activity", icon: "bot" },
  { href: "/history", label: "History", icon: "clock" },
  { href: "/settings", label: "Settings", icon: "gear" },
];

export function Sidebar({ open, onClose }: { open: boolean; onClose: () => void }) {
  const path = usePathname();
  const { recent, recentHidden, hideRecent } = useResearch();
  const showRecent = !recentHidden && recent.length > 0;

  return (
    <>
      {open && <div className="scrim" onClick={onClose} />}
      <aside className={`sidebar ${open ? "sidebar-open" : ""}`}>
        <nav aria-label="Main">
          {NAV.map((n) => (
            <Link key={n.href} href={n.href} onClick={onClose}
              className={`nav-item ${path === n.href || (n.href === "/history" && path.startsWith("/history")) ? "active" : ""}`}>
              <Icon name={n.icon} /> {n.label}
            </Link>
          ))}
        </nav>

        {showRecent && (
          <div className="recent">
            <div className="recent-head">
              <span><Icon name="clock" size={14} /> Recent Searches</span>
              <button onClick={hideRecent} title="Hides this list on this device. Your history is kept.">Clear All</button>
            </div>
            <ul>
              {recent.map((r) => (
                <li key={r.id}><Link href={`/history/${r.id}`} onClick={onClose}>{preview(r.question, 34)}</Link></li>
              ))}
            </ul>
          </div>
        )}

        <div className="tagline"><Icon name="leaf" size={22} /><p>Better questions.<br />Deeper knowledge.</p></div>
      </aside>
    </>
  );
}
