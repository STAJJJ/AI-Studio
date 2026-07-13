import type { FaceSwapTaskResponse, FilePurpose, FileUploadResponse } from "@/types/face-swap";
import type { GenerateImageRequest, GenerateImageResponse, ImageGenerationStatusResponse } from "@/types/image";

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

async function requestForm<TResponse>(path: string, formData: FormData): Promise<TResponse> {
  const response = await fetch(path, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed with status ${response.status}`);
  }

  return (await response.json()) as TResponse;
}

export function resolveApiAssetUrl(path: string | null): string | null {
  if (!path) {
    return null;
  }

  if (path.startsWith("http://") || path.startsWith("https://")) {
    return path;
  }

  return path.startsWith("/") ? path : `/${path}`;
}

export function generateImage(payload: GenerateImageRequest): Promise<GenerateImageResponse> {
  return requestJson<GenerateImageResponse>("/api/v1/images/generate", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getImageGenerationStatus(taskId: string): Promise<ImageGenerationStatusResponse> {
  return requestJson<ImageGenerationStatusResponse>(`/api/v1/images/tasks/${encodeURIComponent(taskId)}`, {
    method: "GET",
  });
}

export function uploadFile(file: File, purpose: FilePurpose): Promise<FileUploadResponse> {
  const formData = new FormData();
  formData.append("purpose", purpose);
  formData.append("file", file);
  return requestForm<FileUploadResponse>("/api/v1/files", formData);
}

export function createFaceSwapTask(sourceFileId: string, targetFileId: string): Promise<FaceSwapTaskResponse> {
  return requestJson<FaceSwapTaskResponse>("/api/v1/face-swap/tasks", {
    method: "POST",
    body: JSON.stringify({ source_file_id: sourceFileId, target_file_id: targetFileId }),
  });
}

export function getTask(taskId: string): Promise<FaceSwapTaskResponse> {
  return requestJson<FaceSwapTaskResponse>(`/api/v1/tasks/${encodeURIComponent(taskId)}`, {
    method: "GET",
  });
}
