import { Suspense } from "react";

import { HistoryPanel } from "@/components/history-panel";

export default function HistoryPage() {
  return (
    <Suspense fallback={<HistoryFallback />}>
      <HistoryPanel />
    </Suspense>
  );
}

function HistoryFallback() {
  return (
    <main className="mx-auto flex w-full max-w-7xl flex-col gap-6 px-6 py-8">
      <div className="space-y-2">
        <p className="text-sm font-medium uppercase tracking-wide text-primary">Workflow History</p>
        <h1 className="text-3xl font-semibold tracking-normal">Recent AI Studio Runs</h1>
        <p className="text-sm text-muted-foreground">Loading workflow history...</p>
      </div>
    </main>
  );
}
