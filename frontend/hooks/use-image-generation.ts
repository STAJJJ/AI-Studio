"use client";

import { useEffect, useRef, useState } from "react";

import { generateImage, getImageGenerationStatus } from "@/services/api";
import type { GenerateImageRequest, GenerateImageResponse, ImageGenerationStatusResponse } from "@/types/image";

type ImageGenerationPhase = "idle" | "generating" | "completed" | "failed";

interface UseImageGenerationResult {
  phase: ImageGenerationPhase;
  isGenerating: boolean;
  activeRequest: GenerateImageRequest | null;
  result: GenerateImageResponse | null;
  status: ImageGenerationStatusResponse | null;
  error: string | null;
  submit: (request: GenerateImageRequest) => Promise<void>;
}

const POLL_INTERVAL_MS = 2000;

export function useImageGeneration(): UseImageGenerationResult {
  const [phase, setPhase] = useState<ImageGenerationPhase>("idle");
  const [activeRequest, setActiveRequest] = useState<GenerateImageRequest | null>(null);
  const [result, setResult] = useState<GenerateImageResponse | null>(null);
  const [status, setStatus] = useState<ImageGenerationStatusResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const pollTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const requestTokenRef = useRef(0);
  const isGeneratingRef = useRef(false);

  function clearPollTimer() {
    if (pollTimeoutRef.current !== null) {
      clearTimeout(pollTimeoutRef.current);
      pollTimeoutRef.current = null;
    }
  }

  function finishGeneration() {
    isGeneratingRef.current = false;
    clearPollTimer();
  }

  function schedulePoll(taskId: string, requestToken: number) {
    clearPollTimer();
    pollTimeoutRef.current = setTimeout(() => {
      void pollTask(taskId, requestToken);
    }, POLL_INTERVAL_MS);
  }

  async function pollTask(taskId: string, requestToken: number) {
    if (requestTokenRef.current !== requestToken) {
      return;
    }

    try {
      const nextStatus = await getImageGenerationStatus(taskId);
      if (requestTokenRef.current !== requestToken) {
        return;
      }

      setStatus(nextStatus);

      if (nextStatus.status === "completed") {
        finishGeneration();
        if (nextStatus.image_url) {
          setPhase("completed");
          setError(null);
          window.dispatchEvent(new Event("ai-studio:history-updated"));
        } else {
          setPhase("failed");
          setError("Image generation completed, but ComfyUI did not return an output image.");
        }
        return;
      }

      if (nextStatus.status === "failed") {
        finishGeneration();
        setPhase("failed");
        setError("Image generation failed in ComfyUI. Please retry with the same prompt.");
        return;
      }

      schedulePoll(taskId, requestToken);
    } catch (caught) {
      if (requestTokenRef.current !== requestToken) {
        return;
      }
      finishGeneration();
      setPhase("failed");
      setError(caught instanceof Error ? caught.message : "Image generation status polling failed");
    }
  }

  async function submit(request: GenerateImageRequest) {
    if (isGeneratingRef.current) {
      return;
    }

    isGeneratingRef.current = true;
    requestTokenRef.current += 1;
    const requestToken = requestTokenRef.current;

    clearPollTimer();
    setPhase("generating");
    setActiveRequest(request);
    setError(null);
    setResult(null);
    setStatus(null);

    try {
      const response = await generateImage(request);
      if (requestTokenRef.current !== requestToken) {
        return;
      }

      setResult(response);
      setStatus({ task_id: response.task_id, status: "running", progress: 0, image_url: null });
      schedulePoll(response.task_id, requestToken);
    } catch (caught) {
      if (requestTokenRef.current !== requestToken) {
        return;
      }
      finishGeneration();
      setPhase("failed");
      setError(caught instanceof Error ? caught.message : "Image generation failed");
    }
  }

  useEffect(() => {
    return () => {
      requestTokenRef.current += 1;
      isGeneratingRef.current = false;
      clearPollTimer();
    };
  }, []);

  return { phase, isGenerating: phase === "generating", activeRequest, result, status, error, submit };
}
