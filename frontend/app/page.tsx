"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Images, MessageSquare, Shuffle } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { getRuntime } from "@/services/api";
import type { RuntimeResponse } from "@/types/image";

const fallbackRuntime: RuntimeResponse = {
  current_model: "Stable Diffusion 1.5",
  current_model_id: "sd15",
  engine: "ComfyUI",
  backend: "FastAPI",
  gpu: "Apple Silicon MPS",
  status: "Ready",
  models: [
    { id: "sd15", name: "Stable Diffusion 1.5", width: 512, height: 512 },
    { id: "sdxl-lightning-4step", name: "SDXL Lightning 4-Step", width: 768, height: 768 },
  ],
};

const workspaceCards = [
  {
    href: "/chat",
    title: "AI Chat",
    description: "Streaming conversations through the LLM Gateway with role-based assistants.",
    icon: MessageSquare,
    action: "Open Chat",
    variant: "default" as const,
  },
  {
    href: "/images",
    title: "Text to Image",
    description: "Generate images through ComfyUI workflows and model registry selection.",
    icon: Images,
    action: "Generate Image",
    variant: "default" as const,
  },
  {
    href: "/face-swap",
    title: "Face Swap",
    description: "Run end-to-end FaceFusion image face swap tasks from uploaded files.",
    icon: Shuffle,
    action: "Open Face Swap",
    variant: "secondary" as const,
  },
];

export default function HomePage() {
  const [runtime, setRuntime] = useState<RuntimeResponse>(fallbackRuntime);

  useEffect(() => {
    let isActive = true;
    void getRuntime()
      .then((response) => {
        if (isActive) {
          setRuntime(response);
        }
      })
      .catch(() => {
        if (isActive) {
          setRuntime(fallbackRuntime);
        }
      });
    return () => {
      isActive = false;
    };
  }, []);

  const runtimeStatus = [
    ["Current Model", runtime.current_model],
    ["Engine", runtime.engine],
    ["Backend", runtime.backend],
    ["GPU", runtime.gpu],
  ] as const;

  return (
    <main className="mx-auto flex w-full max-w-6xl flex-col gap-8 px-6 py-8 lg:py-10">
      <section className="space-y-4">
        <p className="text-sm font-medium uppercase tracking-wide text-primary">Workspace</p>
        <div className="max-w-3xl space-y-3">
          <h1 className="text-4xl font-semibold tracking-normal sm:text-5xl">AI Studio</h1>
          <p className="text-base leading-7 text-muted-foreground">
            A local AIGC workspace for Chat, Text to Image, and Face Swap workflows with unified FastAPI services.
          </p>
        </div>
      </section>

      <Card>
        <CardHeader className="pb-4">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <CardTitle className="text-lg">Runtime</CardTitle>
              <CardDescription>Current local execution environment reported by FastAPI.</CardDescription>
            </div>
            <span className="rounded-md border border-secondary/30 bg-secondary/10 px-3 py-1 text-sm font-medium text-secondary">
              {runtime.status}
            </span>
          </div>
        </CardHeader>
        <CardContent>
          <dl className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {runtimeStatus.map(([label, value]) => (
              <div key={label} className="space-y-1 rounded-md border bg-muted/20 p-3">
                <dt className="text-xs font-medium uppercase tracking-wide text-muted-foreground">{label}</dt>
                <dd className="text-sm font-medium text-foreground">{value}</dd>
              </div>
            ))}
          </dl>
        </CardContent>
      </Card>

      <section className="grid gap-4 md:grid-cols-3">
        {workspaceCards.map((item) => {
          const Icon = item.icon;
          return (
            <Card key={item.href} className="flex flex-col transition-colors hover:border-primary/70">
              <CardHeader className="flex-1">
                <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-md bg-primary/10 text-primary">
                  <Icon className="h-5 w-5" aria-hidden="true" />
                </div>
                <CardTitle>{item.title}</CardTitle>
                <CardDescription>{item.description}</CardDescription>
              </CardHeader>
              <CardContent>
                <Button asChild variant={item.variant} className="w-full">
                  <Link href={item.href}>{item.action}</Link>
                </Button>
              </CardContent>
            </Card>
          );
        })}
      </section>
    </main>
  );
}
