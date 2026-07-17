"use client";

import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import { Clock, History, Images, MessageSquare, Shuffle } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useHistory } from "@/hooks/use-history";
import type { WorkflowRunStatus, WorkflowRunSummary, WorkflowType } from "@/types/history";

interface WorkspaceSidebarProps {
  onNavigate?: () => void;
}

const navItems = [
  { href: "/chat", label: "AI Chat", icon: MessageSquare },
  { href: "/images", label: "Text to Image", icon: Images },
  { href: "/face-swap", label: "Face Swap", icon: Shuffle },
];

const workflowIcon: Record<WorkflowType, typeof Images> = {
  image_generation: Images,
  face_swap: Shuffle,
};

const statusTone: Record<WorkflowRunStatus, "default" | "success" | "warning" | "danger" | "muted"> = {
  pending: "muted",
  running: "warning",
  succeeded: "success",
  failed: "danger",
};

export function WorkspaceSidebar({ onNavigate }: WorkspaceSidebarProps) {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const activeRunId = searchParams.get("run_id");
  const { items, loading, error, refresh } = useHistory({ limit: 10 });

  return (
    <div className="flex h-full min-h-screen flex-col">
      <div className="border-b p-5">
        <Link href="/" onClick={onNavigate} className="block space-y-1">
          <p className="text-lg font-semibold tracking-normal">AI Studio</p>
          <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">AI Workspace</p>
        </Link>
      </div>

      <div className="flex-1 overflow-y-auto px-3 py-4">
        <section className="space-y-2">
          <p className="px-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">Workspace</p>
          <nav className="space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const active = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={onNavigate}
                  className={[
                    "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                    active ? "bg-primary text-primary-foreground" : "text-foreground hover:bg-muted",
                  ].join(" ")}
                >
                  <Icon className="h-4 w-4" aria-hidden="true" />
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </section>

        <section className="mt-7 space-y-3">
          <div className="flex items-center justify-between gap-2 px-2">
            <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Recent Workflows</p>
            <button type="button" onClick={() => void refresh()} className="text-xs text-muted-foreground hover:text-foreground">
              Refresh
            </button>
          </div>

          {loading ? <p className="px-2 text-sm text-muted-foreground">Loading history...</p> : null}
          {error ? (
            <div className="space-y-2 rounded-md border border-destructive/30 bg-destructive/10 p-3">
              <p className="text-xs text-destructive">Unable to load history.</p>
              <Button type="button" size="sm" variant="outline" onClick={() => void refresh()}>Retry</Button>
            </div>
          ) : null}
          {!loading && !error && items.length === 0 ? (
            <p className="px-2 text-sm leading-6 text-muted-foreground">No workflow runs yet.</p>
          ) : null}

          <div className="space-y-1">
            {items.map((item) => (
              <RecentWorkflowItem
                key={item.id}
                item={item}
                active={pathname === "/history" && activeRunId === item.id}
                onNavigate={onNavigate}
              />
            ))}
          </div>
        </section>
      </div>

      <div className="border-t p-3">
        <Button asChild variant="outline" className="w-full justify-start">
          <Link href="/history" onClick={onNavigate}>
            <History className="h-4 w-4" aria-hidden="true" />
            View all history
          </Link>
        </Button>
      </div>
    </div>
  );
}

function RecentWorkflowItem({ item, active, onNavigate }: { item: WorkflowRunSummary; active: boolean; onNavigate?: () => void }) {
  const Icon = workflowIcon[item.workflow_type];

  return (
    <Link
      href={`/history?run_id=${encodeURIComponent(item.id)}`}
      onClick={onNavigate}
      className={[
        "block rounded-md border px-3 py-2 transition-colors",
        active ? "border-primary bg-primary/10" : "border-transparent hover:border-border hover:bg-muted/50",
      ].join(" ")}
    >
      <div className="flex items-start gap-2">
        <div className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-muted text-muted-foreground">
          <Icon className="h-3.5 w-3.5" aria-hidden="true" />
        </div>
        <div className="min-w-0 flex-1 space-y-1">
          <p className="truncate text-sm font-medium text-foreground">{item.title}</p>
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Clock className="h-3 w-3" aria-hidden="true" />
            <span>{formatRelativeTime(item.created_at)}</span>
            <Badge tone={statusTone[item.status]} className="px-1.5 py-0 text-[10px]">
              {item.status}
            </Badge>
          </div>
        </div>
      </div>
    </Link>
  );
}

function formatRelativeTime(timestamp: number): string {
  const seconds = Math.max(0, Math.floor(Date.now() / 1000 - timestamp));
  if (seconds < 60) return "just now";
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 7) return `${days}d ago`;
  return new Intl.DateTimeFormat(undefined, { month: "short", day: "2-digit" }).format(new Date(timestamp * 1000));
}
