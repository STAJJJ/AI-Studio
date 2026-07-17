"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Download, History, RefreshCw } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { useHistory } from "@/hooks/use-history";
import { resolveApiAssetUrl } from "@/services/api";
import type { HistoryFilters, WorkflowRunStatus, WorkflowRunSummary, WorkflowType } from "@/types/history";

const workflowTypeOptions: Array<{ label: string; value: HistoryFilters["workflowType"] }> = [
  { label: "All", value: "all" },
  { label: "Image Generation", value: "image_generation" },
  { label: "Face Swap", value: "face_swap" },
];

const statusOptions: Array<{ label: string; value: HistoryFilters["status"] }> = [
  { label: "All", value: "all" },
  { label: "Pending", value: "pending" },
  { label: "Running", value: "running" },
  { label: "Succeeded", value: "succeeded" },
  { label: "Failed", value: "failed" },
];

const statusTone: Record<WorkflowRunStatus, "default" | "success" | "warning" | "danger" | "muted"> = {
  pending: "muted",
  running: "warning",
  succeeded: "success",
  failed: "danger",
};

const workflowLabel: Record<WorkflowType, string> = {
  image_generation: "Image Generation",
  face_swap: "Face Swap",
};

export function HistoryPanel() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const runId = searchParams.get("run_id");
  const {
    filters,
    items,
    total,
    selectedRun,
    loading,
    detailLoading,
    error,
    setWorkflowType,
    setStatus,
    selectRun,
    refresh,
  } = useHistory({ initialRunId: runId });
  const resultUrl = resolveApiAssetUrl(selectedRun?.result_url ?? null);
  const detailError = runId && !selectedRun && error ? error : null;

  function handleSelectRun(runId: string) {
    router.push(`/history?run_id=${encodeURIComponent(runId)}`);
    void selectRun(runId);
  }

  return (
    <main className="mx-auto flex w-full max-w-7xl flex-col gap-6 px-6 py-8">
      <header className="flex flex-wrap items-center justify-between gap-4">
        <div className="space-y-1">
          <p className="text-sm font-medium uppercase tracking-wide text-primary">Workflow History</p>
          <h1 className="text-3xl font-semibold tracking-normal">Recent AI Studio Runs</h1>
          <p className="text-sm text-muted-foreground">Browser-visible history for image generation and face swap workflows.</p>
        </div>
        <div className="flex flex-wrap gap-3">
          <Button type="button" variant="outline" onClick={() => void refresh()}>
            <RefreshCw className="h-4 w-4" aria-hidden="true" />
            Refresh
          </Button>
        </div>
      </header>

      <section className="grid flex-1 gap-6 lg:grid-cols-[440px_1fr]">
        <Card>
          <CardHeader>
            <CardTitle>Runs</CardTitle>
            <CardDescription>{loading ? "Loading workflow history..." : `${total} run${total === 1 ? "" : "s"} found.`}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-5">
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="workflow-type">Workflow</Label>
                <select
                  id="workflow-type"
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm outline-none transition-colors focus-visible:ring-2 focus-visible:ring-ring"
                  value={filters.workflowType}
                  onChange={(event) => setWorkflowType(event.target.value as HistoryFilters["workflowType"])}
                >
                  {workflowTypeOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="workflow-status">Status</Label>
                <select
                  id="workflow-status"
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm outline-none transition-colors focus-visible:ring-2 focus-visible:ring-ring"
                  value={filters.status}
                  onChange={(event) => setStatus(event.target.value as HistoryFilters["status"])}
                >
                  {statusOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {error ? (
              <div className="space-y-3 rounded-md border border-destructive/30 bg-destructive/10 p-3">
                <p className="text-sm text-destructive">{error}</p>
                <Button type="button" variant="outline" size="sm" onClick={() => void refresh()}>
                  Retry
                </Button>
              </div>
            ) : null}

            {loading ? <p className="rounded-md bg-muted px-3 py-3 text-sm text-muted-foreground">Loading...</p> : null}

            {!loading && items.length === 0 ? (
              <div className="rounded-lg border border-dashed bg-muted/30 p-8 text-center">
                <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-md bg-primary/10 text-primary">
                  <History className="h-5 w-5" aria-hidden="true" />
                </div>
                <p className="text-sm text-muted-foreground">No workflow runs match the current filters.</p>
              </div>
            ) : null}

            <div className="space-y-3">
              {items.map((item) => (
                <HistoryListItem
                  key={item.id}
                  item={item}
                  selected={selectedRun?.id === item.id}
                  onSelect={() => handleSelectRun(item.id)}
                />
              ))}
            </div>
          </CardContent>
        </Card>

        <Card className="min-h-[620px]">
          <CardHeader>
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <CardTitle>{selectedRun ? selectedRun.title : "Run Detail"}</CardTitle>
                <CardDescription>Inspect controlled inputs, runtime metadata, status, and result.</CardDescription>
              </div>
              {selectedRun ? <Badge tone={statusTone[selectedRun.status]}>{selectedRun.status}</Badge> : null}
            </div>
          </CardHeader>
          <CardContent>
            {!selectedRun && !detailLoading ? (
              <div className={[
                "flex min-h-96 items-center justify-center rounded-lg border border-dashed p-6 text-center",
                detailError ? "border-destructive/30 bg-destructive/5" : "bg-muted/30",
              ].join(" ")}>
                <div className="max-w-md space-y-2">
                  <p className={detailError ? "text-sm font-medium text-destructive" : "text-sm text-muted-foreground"}>
                    {detailError ? "Workflow run not found" : "Select a workflow run to view details, preview output, or download the result."}
                  </p>
                  {detailError ? <p className="text-sm text-destructive/90">{detailError}</p> : null}
                </div>
              </div>
            ) : null}

            {detailLoading ? <p className="rounded-md bg-muted px-3 py-3 text-sm text-muted-foreground">Loading detail...</p> : null}

            {selectedRun ? (
              <div className="space-y-5">
                {resultUrl ? (
                  <div className="overflow-hidden rounded-md border bg-background">
                    <img className="max-h-[520px] w-full object-contain" src={resultUrl} alt={`${selectedRun.title} result`} />
                  </div>
                ) : (
                  <div className="rounded-lg border border-dashed bg-muted/30 p-8 text-center text-sm text-muted-foreground">No result available yet.</div>
                )}

                <div className="grid gap-4 rounded-lg border bg-card p-5 md:grid-cols-2">
                  <InfoRow label="Run ID" value={selectedRun.id} mono />
                  <InfoRow label="External Task" value={selectedRun.external_task_id} mono />
                  <InfoRow label="Workflow" value={workflowLabel[selectedRun.workflow_type]} />
                  <InfoRow label="Runtime" value={`${selectedRun.runtime} / ${selectedRun.provider}`} />
                  <InfoRow label="Progress" value={`${selectedRun.progress}%`} />
                  <InfoRow label="Created" value={formatTimestamp(selectedRun.created_at)} />
                </div>

                <div className="grid gap-4 md:grid-cols-2">
                  <PayloadBlock title="Input Payload" payload={selectedRun.input_payload} />
                  <PayloadBlock title="Output Payload" payload={selectedRun.output_payload} />
                </div>

                {selectedRun.error_message ? (
                  <div className="rounded-md border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
                    {selectedRun.error_code ? `${selectedRun.error_code}: ` : ""}
                    {selectedRun.error_message}
                  </div>
                ) : null}

                {resultUrl ? (
                  <Button asChild variant="outline">
                    <a href={resultUrl} download>
                      <Download className="h-4 w-4" aria-hidden="true" />
                      Download Result
                    </a>
                  </Button>
                ) : null}
              </div>
            ) : null}
          </CardContent>
        </Card>
      </section>
    </main>
  );
}

function HistoryListItem({ item, selected, onSelect }: { item: WorkflowRunSummary; selected: boolean; onSelect: () => void }) {
  return (
    <button
      type="button"
      onClick={onSelect}
      className={[
        "w-full rounded-lg border bg-background p-4 text-left transition-colors hover:border-primary/70",
        selected ? "border-primary ring-2 ring-ring" : "",
      ].join(" ")}
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0 space-y-1">
          <p className="truncate text-sm font-medium text-foreground">{item.title}</p>
          <p className="line-clamp-2 text-sm leading-6 text-muted-foreground">{item.input_summary}</p>
        </div>
        <Badge tone={statusTone[item.status]}>{item.status}</Badge>
      </div>
      <div className="mt-3 flex flex-wrap gap-2 text-xs text-muted-foreground">
        <span>{workflowLabel[item.workflow_type]}</span>
        <span>•</span>
        <span>{item.runtime}</span>
        <span>•</span>
        <span>{item.provider}</span>
        <span>•</span>
        <span>{formatTimestamp(item.created_at)}</span>
      </div>
    </button>
  );
}

function InfoRow({ label, value, mono = false }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="space-y-1">
      <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">{label}</p>
      <p className={["break-words text-sm font-medium text-foreground", mono ? "font-mono" : ""].join(" ")}>{value}</p>
    </div>
  );
}

function PayloadBlock({ title, payload }: { title: string; payload: Record<string, unknown> }) {
  return (
    <div className="rounded-lg border bg-muted/20 p-4">
      <p className="mb-3 text-sm font-medium text-foreground">{title}</p>
      <pre className="max-h-72 overflow-auto whitespace-pre-wrap break-words text-xs leading-6 text-muted-foreground">
        {JSON.stringify(payload, null, 2)}
      </pre>
    </div>
  );
}

function formatTimestamp(value: number): string {
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value * 1000));
}
