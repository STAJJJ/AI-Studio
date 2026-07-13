import Link from "next/link";
import { Images, Shuffle } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

const runtimeStatus = [
  ["Current Model", "FLUX.1 Schnell FP8"],
  ["Engine", "ComfyUI"],
  ["Backend", "FastAPI"],
  ["GPU", "RTX 4090 D"],
] as const;

export default function HomePage() {
  return (
    <main className="mx-auto flex min-h-screen w-full max-w-5xl flex-col px-6 py-10">
      <section className="flex flex-1 flex-col justify-center gap-8">
        <div className="space-y-3">
          <p className="text-sm font-medium uppercase tracking-wide text-primary">Web Demo</p>
          <h1 className="text-4xl font-semibold tracking-normal sm:text-5xl">AI Studio</h1>
          <p className="max-w-2xl text-base leading-7 text-muted-foreground">
            A compact AIGC workspace for validating text-to-image and future face swap workflows.
          </p>
        </div>

        <Card>
          <CardHeader className="pb-4">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <CardTitle className="text-lg">Runtime</CardTitle>
                <CardDescription>Static demo environment for the current image generation workflow.</CardDescription>
              </div>
              <span className="rounded-md border border-secondary/30 bg-secondary/10 px-3 py-1 text-sm font-medium text-secondary">
                Ready
              </span>
            </div>
          </CardHeader>
          <CardContent>
            <dl className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {runtimeStatus.map(([label, value]) => (
                <div key={label} className="space-y-1">
                  <dt className="text-xs font-medium uppercase tracking-wide text-muted-foreground">{label}</dt>
                  <dd className="text-sm font-medium text-foreground">{value}</dd>
                </div>
              ))}
            </dl>
          </CardContent>
        </Card>

        <div className="grid gap-4 md:grid-cols-2">
          <Card className="transition-colors hover:border-primary/70">
            <CardHeader>
              <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-md bg-primary/10 text-primary">
                <Images className="h-5 w-5" aria-hidden="true" />
              </div>
              <CardTitle>Text to Image</CardTitle>
              <CardDescription>Generate an image task through the FastAPI ComfyUI gateway.</CardDescription>
            </CardHeader>
            <CardContent>
              <Button asChild>
                <Link href="/images">Open</Link>
              </Button>
            </CardContent>
          </Card>

          <Card className="opacity-70">
            <CardHeader>
              <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-md bg-secondary/10 text-secondary">
                <Shuffle className="h-5 w-5" aria-hidden="true" />
              </div>
              <CardTitle>Face Swap</CardTitle>
              <CardDescription>Coming Soon</CardDescription>
            </CardHeader>
            <CardContent>
              <Button disabled variant="secondary">
                Coming Soon
              </Button>
            </CardContent>
          </Card>
        </div>
      </section>
    </main>
  );
}
