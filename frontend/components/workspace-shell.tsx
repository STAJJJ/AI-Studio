"use client";

import { ReactNode, Suspense, useState } from "react";
import { Menu } from "lucide-react";

import { Button } from "@/components/ui/button";
import { WorkspaceSidebar } from "@/components/workspace-sidebar";

interface WorkspaceShellProps {
  children: ReactNode;
}

export function WorkspaceShell({ children }: WorkspaceShellProps) {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className="min-h-screen overflow-x-hidden bg-background text-foreground">
      <div className="lg:hidden">
        <div className="fixed left-0 right-0 top-0 z-40 flex h-14 w-screen items-center gap-3 border-b bg-background/95 px-4 backdrop-blur">
          <Button type="button" variant="outline" size="sm" onClick={() => setMobileOpen(true)} aria-label="Open sidebar">
            <Menu className="h-4 w-4" aria-hidden="true" />
          </Button>
          <div className="space-y-0.5">
            <p className="text-sm font-semibold">AI Studio</p>
            <p className="text-xs text-muted-foreground">AI Workspace</p>
          </div>
        </div>
        <div className="h-14" />
      </div>

      <div className="flex min-h-screen">
        <aside className="hidden w-72 shrink-0 border-r bg-card lg:block">
          <Suspense fallback={<SidebarFallback />}>
            <WorkspaceSidebar onNavigate={() => setMobileOpen(false)} />
          </Suspense>
        </aside>
        <main className="min-w-0 flex-1">{children}</main>
      </div>

      {mobileOpen ? (
        <div className="fixed inset-0 z-50 lg:hidden">
          <button
            type="button"
            aria-label="Close sidebar"
            className="absolute inset-0 bg-foreground/20"
            onClick={() => setMobileOpen(false)}
          />
          <aside className="relative h-full w-[min(88vw,320px)] border-r bg-card shadow-xl">
            <Suspense fallback={<SidebarFallback />}>
              <WorkspaceSidebar onNavigate={() => setMobileOpen(false)} />
            </Suspense>
          </aside>
        </div>
      ) : null}
    </div>
  );
}

function SidebarFallback() {
  return (
    <div className="flex h-full min-h-screen flex-col">
      <div className="border-b p-5">
        <p className="text-lg font-semibold tracking-normal">AI Studio</p>
        <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">AI Workspace</p>
      </div>
      <div className="space-y-3 px-5 py-4">
        <div className="h-9 rounded-md bg-muted" />
        <div className="h-9 rounded-md bg-muted" />
        <div className="h-9 rounded-md bg-muted" />
      </div>
    </div>
  );
}
