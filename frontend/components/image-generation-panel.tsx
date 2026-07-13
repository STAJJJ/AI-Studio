"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import { ArrowLeft, Download, Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { useImageGeneration } from "@/hooks/use-image-generation";

const defaultPrompt =
  "A cinematic portrait of a young man in a modern photography studio, realistic skin texture, soft lighting, detailed face, professional photography";

export function ImageGenerationPanel() {
  const [prompt, setPrompt] = useState(defaultPrompt);
  const [width, setWidth] = useState(1024);
  const [height, setHeight] = useState(1024);
  const { phase, isGenerating, result, status, error, submit } = useImageGeneration();

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await submit({ prompt, width, height });
  }

  const imageUrl = status?.status === "completed" ? status.image_url : null;

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-7xl flex-col gap-6 px-6 py-8">
      <header className="flex items-center justify-between gap-4">
        <div>
          <p className="text-sm font-medium uppercase tracking-wide text-primary">Text to Image</p>
          <h1 className="mt-1 text-3xl font-semibold tracking-normal">Generate Image</h1>
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
            <CardTitle>Prompt</CardTitle>
            <CardDescription>Submit a ComfyUI FLUX task through FastAPI.</CardDescription>
          </CardHeader>
          <CardContent>
            <form className="space-y-5" onSubmit={handleSubmit}>
              <div className="space-y-2">
                <Label htmlFor="prompt">Prompt</Label>
                <Textarea
                  id="prompt"
                  value={prompt}
                  onChange={(event) => setPrompt(event.target.value)}
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

              <Button className="w-full" disabled={isGenerating || prompt.trim().length === 0} type="submit">
                {isGenerating ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" /> : null}
                {isGenerating ? "Generating" : "Generate"}
              </Button>
            </form>
          </CardContent>
        </Card>

        <Card className="min-h-[480px]">
          <CardHeader>
            <CardTitle>Result</CardTitle>
            <CardDescription>Task response and generated image.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex min-h-80 items-center justify-center rounded-lg border border-dashed bg-muted/40 p-6">
              {phase === "idle" ? (
                <p className="text-center text-sm text-muted-foreground">Generated task details will appear here.</p>
              ) : phase === "failed" ? (
                <div className="w-full max-w-xl rounded-lg border border-destructive/30 bg-destructive/5 p-5 text-sm text-destructive">
                  {error ?? "Image generation failed."}
                </div>
              ) : (
                <div className="w-full max-w-2xl rounded-lg border bg-card p-5">
                  <div className="space-y-4">
                    {result ? (
                      <div>
                        <p className="text-sm text-muted-foreground">Task ID</p>
                        <p className="mt-1 break-all font-mono text-sm">{result.task_id}</p>
                      </div>
                    ) : null}
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <div>
                        <p className="text-sm text-muted-foreground">Status</p>
                        <p className="mt-1 text-sm font-medium capitalize text-secondary">{phase}</p>
                      </div>
                      {status ? (
                        <p className="text-sm text-muted-foreground">Progress {status.progress}%</p>
                      ) : null}
                    </div>

                    {phase === "generating" ? (
                      <div className="flex items-center gap-2 rounded-md bg-muted px-3 py-2 text-sm text-muted-foreground">
                        <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
                        Waiting for ComfyUI result
                      </div>
                    ) : null}

                    {imageUrl ? (
                      <div className="space-y-4">
                        <div className="overflow-hidden rounded-md border bg-background">
                          <img className="h-auto w-full" src={imageUrl} alt="Generated image" />
                        </div>
                        <Button asChild variant="outline">
                          <a href={imageUrl} download>
                            <Download className="h-4 w-4" aria-hidden="true" />
                            Download
                          </a>
                        </Button>
                      </div>
                    ) : null}
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </section>
    </main>
  );
}
