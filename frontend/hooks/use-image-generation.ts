"use client";

import { useState } from "react";

import { generateImage } from "@/services/api";
import type { GenerateImageRequest, GenerateImageResponse } from "@/types/image";

interface UseImageGenerationResult {
  isGenerating: boolean;
  result: GenerateImageResponse | null;
  error: string | null;
  submit: (request: GenerateImageRequest) => Promise<void>;
}

export function useImageGeneration(): UseImageGenerationResult {
  const [isGenerating, setIsGenerating] = useState(false);
  const [result, setResult] = useState<GenerateImageResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function submit(request: GenerateImageRequest) {
    setIsGenerating(true);
    setError(null);
    setResult(null);

    try {
      const response = await generateImage(request);
      setResult(response);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Image generation failed");
    } finally {
      setIsGenerating(false);
    }
  }

  return { isGenerating, result, error, submit };
}
