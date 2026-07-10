import type { GenerateImageRequest, GenerateImageResponse } from "@/types/image";

async function requestJson<TResponse>(path: string, init: RequestInit): Promise<TResponse> {
  const response = await fetch(path, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init.headers,
    },
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed with status ${response.status}`);
  }

  return (await response.json()) as TResponse;
}

export function generateImage(payload: GenerateImageRequest): Promise<GenerateImageResponse> {
  return requestJson<GenerateImageResponse>("/api/v1/images/generate", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
