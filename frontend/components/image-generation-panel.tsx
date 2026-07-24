"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { Download, RefreshCw, Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { useImageGeneration } from "@/hooks/use-image-generation";
import { getRuntime, resolveApiAssetUrl } from "@/services/api";
import type { GenerateImageRequest, RuntimeModel } from "@/types/image";

const fallbackModels: RuntimeModel[] = [
  { id: "sd15", name: "Stable Diffusion 1.5", width: 512, height: 512 },
  { id: "sdxl-lightning-4step", name: "SDXL Lightning 4-Step", width: 768, height: 768 },
];
const defaultPrompt =
  "A cinematic portrait of a young man in a modern studio, realistic photography, soft lighting, detailed face";

const statusCopy = {
  idle: {
    title: "Ready to generate",
    description: "Enter a prompt and submit an image task through the AI Studio gateway.",
  },
  generating: {
    title: "Generating image",
    description: "ComfyUI is processing the prompt. This can take a few minutes on first model load.",
  },
  completed: {
    title: "Image ready",
    description: "The generated PNG is available for preview and download.",
  },
  failed: {
    title: "Generation failed",
    description: "The image task did not complete successfully.",
  },
} as const;

function formatDimensions(request: GenerateImageRequest | null): string {
  if (!request) {
    return "-";
  }

  return `${request.width} x ${request.height}`;
}

export function ImageGenerationPanel() {
  const [models, setModels] = useState<RuntimeModel[]>(fallbackModels);
  const [selectedModelId, setSelectedModelId] = useState("sd15");
  const [prompt, setPrompt] = useState(defaultPrompt);
  const [width, setWidth] = useState(512);
  const [height, setHeight] = useState(512);
  const { phase, isGenerating, activeRequest, result, status, error, submit } = useImageGeneration();

  const selectedModel = useMemo(
    () => models.find((model) => model.id === selectedModelId) ?? fallbackModels[0],
    [models, selectedModelId],
  );
  const imageUrl = useMemo(
    () => resolveApiAssetUrl(status?.status === "completed" ? status.image_url : null),
    [status],
  );
  const taskId = result?.task_id ?? status?.task_id ?? null;
  const progress = status?.progress ?? (phase === "generating" ? 0 : null);
  const canSubmit = !isGenerating && prompt.trim().length > 0;
  const submittedPrompt = activeRequest?.prompt ?? prompt;

  useEffect(() => {
    let isActive = true;
    void getRuntime()
      .then((runtime) => {
        if (!isActive) {
          return;
        }
        setModels(runtime.models);
        setSelectedModelId(runtime.current_model_id);
        const currentModel = runtime.models.find((model) => model.id === runtime.current_model_id);
        if (currentModel) {
          setWidth(currentModel.width);
          setHeight(currentModel.height);
        }
      })
      .catch(() => {
        if (isActive) {
          setModels(fallbackModels);
        }
      });
    return () => {
      isActive = false;
    };
  }, []);

  function handleModelChange(modelId: string) {
    setSelectedModelId(modelId);
    const nextModel = models.find((model) => model.id === modelId);
    if (nextModel) {
      setWidth(nextModel.width);
      setHeight(nextModel.height);
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!canSubmit) {
      return;
    }

    await submit({ prompt: prompt.trim(), model: selectedModelId, width, height });
  }

  async function handleGenerateAgain() {
    if (!canSubmit) {
      return;
    }

    await submit({ prompt: prompt.trim(), model: selectedModelId, width, height });
  }

  async function handleRetry() {
    const retryRequest = activeRequest ?? { prompt: prompt.trim(), model: selectedModelId, width, height };
    if (isGenerating || retryRequest.prompt.trim().length === 0) {
      return;
    }

    await submit(retryRequest);
  }

  return (
    <main className="mx-auto flex w-full max-w-7xl flex-col gap-6 px-6 py-8">
      <header className="space-y-1">
        <div className="space-y-1">
          <p className="text-sm font-medium uppercase tracking-wide text-primary">Text to Image</p>
          <h1 className="text-3xl font-semibold tracking-normal">Generate Image</h1>
          <p className="text-sm text-muted-foreground">Current Model: {selectedModel.name}</p>
        </div>
      </header>

      <section className="grid flex-1 gap-6 lg:grid-cols-[420px_1fr]">
        <Card>
          <CardHeader>
            <CardTitle>Prompt</CardTitle>
            <CardDescription>Submit one ComfyUI image task at a time through FastAPI.</CardDescription>
          </CardHeader>
          <CardContent>
            <form className="space-y-5" onSubmit={handleSubmit}>
              <div className="space-y-2">
                <Label htmlFor="model">Model</Label>
                <select
                  id="model"
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm outline-none transition-colors focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
                  disabled={isGenerating}
                  value={selectedModelId}
                  onChange={(event) => handleModelChange(event.target.value)}
                >
                  {models.map((model) => (
                    <option key={model.id} value={model.id}>
                      {model.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="prompt">Prompt</Label>
                <Textarea
                  id="prompt"
                  value={prompt}
                  onChange={(event) => setPrompt(event.target.value)}
                  placeholder="Describe the image you want to generate"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="width">Width</Label>
                  <Input
                    id="width"
                    type="number"
                    min={64}
                    max={2048}
                    step={8}
                    value={width}
                    onChange={(event) => setWidth(Number(event.target.value))}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="height">Height</Label>
                  <Input
                    id="height"
                    type="number"
                    min={64}
                    max={2048}
                    step={8}
                    value={height}
                    onChange={(event) => setHeight(Number(event.target.value))}
                    required
                  />
                </div>
              </div>

              <Button className="w-full" disabled={!canSubmit} type="submit">
                <Sparkles className="h-4 w-4" aria-hidden="true" />
                {isGenerating ? "Generating..." : "Generate"}
              </Button>
            </form>
          </CardContent>
        </Card>

        <Card className="min-h-[560px]">
          <CardHeader>
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <CardTitle>{statusCopy[phase].title}</CardTitle>
                <CardDescription>{statusCopy[phase].description}</CardDescription>
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
                  <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-md bg-primary/10 text-primary">
                    <Sparkles className="h-5 w-5" aria-hidden="true" />
                  </div>
                  <p className="text-sm text-muted-foreground">
                    Your task ID, generation status, image preview, and download action will appear here.
                  </p>
                </div>
              ) : null}

              {phase === "generating" ? (
                <div className="w-full space-y-5 rounded-lg border bg-card p-5">
                  <TaskMeta taskId={taskId} status={status?.status ?? "running"} progress={progress} />
                  <div className="rounded-md bg-muted px-3 py-3 text-sm text-muted-foreground">
                    Waiting for ComfyUI to finish inference. Polling will stop automatically when the task
                    completes or fails.
                  </div>
                </div>
              ) : null}

              {phase === "completed" ? (
                <div className="w-full space-y-5">
                  {imageUrl ? (
                    <div className="overflow-hidden rounded-md border bg-background">
                      <img className="h-auto w-full" src={imageUrl} alt="Generated image preview" />
                    </div>
                  ) : null}

                  <div className="grid gap-4 rounded-lg border bg-card p-5 md:grid-cols-2">
                    <TaskMeta taskId={taskId} status={status?.status ?? "completed"} progress={progress} />
                    <div className="space-y-3">
                      <InfoRow label="Dimensions" value={formatDimensions(activeRequest)} />
                      <InfoRow label="Prompt" value={submittedPrompt} multiline />
                    </div>
                  </div>

                  <div className="flex flex-wrap gap-3">
                    {imageUrl ? (
                      <Button asChild variant="outline">
                        <a href={imageUrl} download>
                          <Download className="h-4 w-4" aria-hidden="true" />
                          Download PNG
                        </a>
                      </Button>
                    ) : null}
                    <Button disabled={!canSubmit} onClick={handleGenerateAgain} type="button">
                      <RefreshCw className="h-4 w-4" aria-hidden="true" />
                      Generate Again
                    </Button>
                  </div>
                </div>
              ) : null}

              {phase === "failed" ? (
                <div className="w-full space-y-5 rounded-lg border border-destructive/30 bg-destructive/5 p-5">
                  <TaskMeta taskId={taskId} status={status?.status ?? "failed"} progress={progress} />
                  <div className="space-y-2">
                    <p className="text-sm font-medium text-destructive">Unable to complete image generation.</p>
                    <p className="text-sm text-destructive/90">
                      {error ?? "Image generation failed. Please retry with the same prompt."}
                    </p>
                  </div>
                  <Button disabled={isGenerating} onClick={handleRetry} type="button" variant="outline">
                    <RefreshCw className="h-4 w-4" aria-hidden="true" />
                    Retry
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

interface TaskMetaProps {
  taskId: string | null;
  status: string;
  progress: number | null;
}

function TaskMeta({ taskId, status, progress }: TaskMetaProps) {
  return (
    <div className="space-y-3">
      <InfoRow label="Task ID" value={taskId ?? "Waiting for task"} mono />
      <InfoRow label="Status" value={status} />
      <InfoRow label="Progress" value={progress === null ? "-" : `${progress}%`} />
    </div>
  );
}

interface InfoRowProps {
  label: string;
  value: string;
  mono?: boolean;
  multiline?: boolean;
}

function InfoRow({ label, value, mono = false, multiline = false }: InfoRowProps) {
  return (
    <div className="space-y-1">
      <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">{label}</p>
      <p
        className={[
          "break-words text-sm font-medium text-foreground",
          mono ? "font-mono" : "",
          multiline ? "leading-6" : "",
        ].join(" ")}
      >
        {value}
      </p>
    </div>
  );
}
