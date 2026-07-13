"use client";

import { ChangeEvent, FormEvent, useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { ArrowLeft, Download, RefreshCw, Shuffle } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { useFaceSwap } from "@/hooks/use-face-swap";
import { resolveApiAssetUrl } from "@/services/api";

const phaseCopy = {
  idle: {
    title: "Ready to swap",
    description: "Upload a source face and target image to start a FaceFusion task.",
  },
  uploading: {
    title: "Uploading files",
    description: "AI Studio is uploading both images before creating the task.",
  },
  generating: {
    title: "Running FaceFusion",
    description: "The backend is executing FaceFusion through the subprocess CLI integration.",
  },
  completed: {
    title: "Face swap ready",
    description: "The generated PNG is ready for preview and download.",
  },
  failed: {
    title: "Face swap failed",
    description: "The task could not be completed. Check the error and try again.",
  },
} as const;

interface PreviewState {
  file: File | null;
  url: string | null;
}

export function FaceSwapPanel() {
  const [source, setSource] = useState<PreviewState>({ file: null, url: null });
  const [target, setTarget] = useState<PreviewState>({ file: null, url: null });
  const previewUrlsRef = useRef<{ source: string | null; target: string | null }>({ source: null, target: null });
  const { phase, isBusy, sourceUpload, targetUpload, task, error, start, reset } = useFaceSwap();

  const resultUrl = useMemo(() => resolveApiAssetUrl(task?.result?.image_url ?? task?.result?.download_url ?? null), [task]);
  const canSubmit = Boolean(source.file && target.file && !isBusy);

  useEffect(() => {
    return () => {
      if (previewUrlsRef.current.source) {
        URL.revokeObjectURL(previewUrlsRef.current.source);
      }
      if (previewUrlsRef.current.target) {
        URL.revokeObjectURL(previewUrlsRef.current.target);
      }
    };
  }, []);

  function updatePreview(kind: "source" | "target", event: ChangeEvent<HTMLInputElement>) {
    const nextFile = event.target.files?.[0] ?? null;
    const setter = kind === "source" ? setSource : setTarget;
    const previousUrl = previewUrlsRef.current[kind];
    if (previousUrl) {
      URL.revokeObjectURL(previousUrl);
    }
    const nextUrl = nextFile ? URL.createObjectURL(nextFile) : null;
    previewUrlsRef.current[kind] = nextUrl;
    setter({ file: nextFile, url: nextUrl });
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!source.file || !target.file || isBusy) {
      return;
    }
    await start({ sourceFile: source.file, targetFile: target.file });
  }

  function handleTryAgain() {
    reset();
  }

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-7xl flex-col gap-6 px-6 py-8">
      <header className="flex flex-wrap items-center justify-between gap-4">
        <div className="space-y-1">
          <p className="text-sm font-medium uppercase tracking-wide text-primary">Face Swap</p>
          <h1 className="text-3xl font-semibold tracking-normal">FaceFusion Demo</h1>
          <p className="text-sm text-muted-foreground">Source face + target image to FaceFusion CLI to PNG result.</p>
        </div>
        <Button asChild variant="outline">
          <Link href="/">
            <ArrowLeft className="h-4 w-4" aria-hidden="true" />
            Home
          </Link>
        </Button>
      </header>

      <section className="grid flex-1 gap-6 lg:grid-cols-[420px_1fr]">
        <Card>
          <CardHeader>
            <CardTitle>Inputs</CardTitle>
            <CardDescription>Upload one source face image and one target image.</CardDescription>
          </CardHeader>
          <CardContent>
            <form className="space-y-5" onSubmit={handleSubmit}>
              <ImagePicker
                id="source-face"
                label="Source Face"
                file={source.file}
                previewUrl={source.url}
                onChange={(event) => updatePreview("source", event)}
              />
              <ImagePicker
                id="target-image"
                label="Target Image"
                file={target.file}
                previewUrl={target.url}
                onChange={(event) => updatePreview("target", event)}
              />

              <Button className="w-full" disabled={!canSubmit} type="submit">
                <Shuffle className="h-4 w-4" aria-hidden="true" />
                {phase === "uploading" ? "Uploading..." : phase === "generating" ? "Generating..." : "Start Face Swap"}
              </Button>
            </form>
          </CardContent>
        </Card>

        <Card className="min-h-[560px]">
          <CardHeader>
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <CardTitle>{phaseCopy[phase].title}</CardTitle>
                <CardDescription>{phaseCopy[phase].description}</CardDescription>
              </div>
              <span className="rounded-md border bg-background px-3 py-1 text-sm font-medium capitalize text-foreground">
                {phase}
              </span>
            </div>
          </CardHeader>
          <CardContent>
            <div className="flex min-h-96 rounded-lg border border-dashed bg-muted/30 p-5">
              {phase === "idle" ? (
                <div className="m-auto max-w-md space-y-3 text-center">
                  <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-md bg-secondary/10 text-secondary">
                    <Shuffle className="h-5 w-5" aria-hidden="true" />
                  </div>
                  <p className="text-sm text-muted-foreground">
                    Task ID, status, result preview, and download action will appear here.
                  </p>
                </div>
              ) : null}

              {phase === "uploading" || phase === "generating" ? (
                <div className="w-full space-y-5 rounded-lg border bg-card p-5">
                  <TaskMeta taskId={task?.task_id ?? null} status={task?.status ?? phase} progress={task?.progress ?? 0} />
                  <div className="grid gap-3 md:grid-cols-2">
                    <InfoRow label="Source File" value={sourceUpload?.id ?? "Uploading"} mono />
                    <InfoRow label="Target File" value={targetUpload?.id ?? "Waiting"} mono />
                  </div>
                  <p className="rounded-md bg-muted px-3 py-3 text-sm text-muted-foreground">
                    Polling runs every 2 seconds and stops automatically when the task succeeds or fails.
                  </p>
                </div>
              ) : null}

              {phase === "completed" ? (
                <div className="w-full space-y-5">
                  {resultUrl ? (
                    <div className="overflow-hidden rounded-md border bg-background">
                      <img className="h-auto w-full" src={resultUrl} alt="Face swap result preview" />
                    </div>
                  ) : null}
                  <div className="grid gap-4 rounded-lg border bg-card p-5 md:grid-cols-2">
                    <TaskMeta taskId={task?.task_id ?? null} status={task?.status ?? "succeeded"} progress={task?.progress ?? 100} />
                    <div className="space-y-3">
                      <InfoRow label="Source Upload" value={sourceUpload?.filename ?? "-"} />
                      <InfoRow label="Target Upload" value={targetUpload?.filename ?? "-"} />
                    </div>
                  </div>
                  <div className="flex flex-wrap gap-3">
                    {resultUrl ? (
                      <Button asChild variant="outline">
                        <a href={resultUrl} download>
                          <Download className="h-4 w-4" aria-hidden="true" />
                          Download PNG
                        </a>
                      </Button>
                    ) : null}
                    <Button onClick={handleTryAgain} type="button">
                      <RefreshCw className="h-4 w-4" aria-hidden="true" />
                      Try Again
                    </Button>
                  </div>
                </div>
              ) : null}

              {phase === "failed" ? (
                <div className="w-full space-y-5 rounded-lg border border-destructive/30 bg-destructive/5 p-5">
                  <TaskMeta taskId={task?.task_id ?? null} status={task?.status ?? "failed"} progress={task?.progress ?? 100} />
                  <div className="space-y-2">
                    <p className="text-sm font-medium text-destructive">Unable to complete face swap.</p>
                    <p className="text-sm text-destructive/90">{error ?? "Face swap failed. Please retry."}</p>
                  </div>
                  <Button onClick={handleTryAgain} type="button" variant="outline">
                    <RefreshCw className="h-4 w-4" aria-hidden="true" />
                    Try Again
                  </Button>
                </div>
              ) : null}
            </div>
          </CardContent>
        </Card>
      </section>
    </main>
  );
}

interface ImagePickerProps {
  id: string;
  label: string;
  file: File | null;
  previewUrl: string | null;
  onChange: (event: ChangeEvent<HTMLInputElement>) => void;
}

function ImagePicker({ id, label, file, previewUrl, onChange }: ImagePickerProps) {
  return (
    <div className="space-y-2">
      <Label htmlFor={id}>{label}</Label>
      <input
        id={id}
        type="file"
        accept="image/png,image/jpeg,image/webp"
        onChange={onChange}
        className="block w-full rounded-md border border-input bg-background px-3 py-2 text-sm file:mr-3 file:rounded-md file:border-0 file:bg-primary file:px-3 file:py-1.5 file:text-sm file:font-medium file:text-primary-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
      />
      <div className="flex min-h-44 items-center justify-center overflow-hidden rounded-md border bg-muted/30">
        {previewUrl ? <img className="h-auto max-h-64 w-full object-contain" src={previewUrl} alt={`${label} preview`} /> : null}
        {!previewUrl ? <p className="text-sm text-muted-foreground">No image selected</p> : null}
      </div>
      {file ? <p className="truncate text-xs text-muted-foreground">{file.name}</p> : null}
    </div>
  );
}

interface TaskMetaProps {
  taskId: string | null;
  status: string;
  progress: number;
}

function TaskMeta({ taskId, status, progress }: TaskMetaProps) {
  return (
    <div className="space-y-3">
      <InfoRow label="Task ID" value={taskId ?? "Waiting for task"} mono />
      <InfoRow label="Status" value={status} />
      <InfoRow label="Progress" value={`${progress}%`} />
    </div>
  );
}

interface InfoRowProps {
  label: string;
  value: string;
  mono?: boolean;
}

function InfoRow({ label, value, mono = false }: InfoRowProps) {
  return (
    <div className="space-y-1">
      <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">{label}</p>
      <p className={["break-words text-sm font-medium text-foreground", mono ? "font-mono" : ""].join(" ")}>{value}</p>
    </div>
  );
}
