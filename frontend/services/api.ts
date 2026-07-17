import type { FaceSwapTaskResponse, FilePurpose, FileUploadResponse } from "@/types/face-swap";
import type { ChatCompletionRequest, ChatRolesResponse, ChatStreamEvent } from "@/types/chat";
import type { WorkflowHistoryListResponse, WorkflowRunDetail, WorkflowRunStatus, WorkflowType } from "@/types/history";
import type {
  GenerateImageRequest,
  GenerateImageResponse,
  ImageGenerationStatusResponse,
  RuntimeResponse,
} from "@/types/image";

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
    throw new Error(extractErrorMessage(message) || `Request failed with status ${response.status}`);
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
    throw new Error(extractErrorMessage(message) || `Request failed with status ${response.status}`);
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


export function getWorkflowHistory(params: {
  workflowType?: WorkflowType;
  status?: WorkflowRunStatus;
  limit?: number;
  offset?: number;
} = {}): Promise<WorkflowHistoryListResponse> {
  const searchParams = new URLSearchParams();
  if (params.workflowType) {
    searchParams.set("workflow_type", params.workflowType);
  }
  if (params.status) {
    searchParams.set("status", params.status);
  }
  searchParams.set("limit", String(params.limit ?? 20));
  searchParams.set("offset", String(params.offset ?? 0));
  const query = searchParams.toString();
  return requestJson<WorkflowHistoryListResponse>(`/api/v1/history${query ? `?${query}` : ""}`, {
    method: "GET",
  });
}

export function getWorkflowHistoryRun(runId: string): Promise<WorkflowRunDetail> {
  return requestJson<WorkflowRunDetail>(`/api/v1/history/${encodeURIComponent(runId)}`, {
    method: "GET",
  });
}

export function getRuntime(): Promise<RuntimeResponse> {
  return requestJson<RuntimeResponse>("/api/v1/runtime", {
    method: "GET",
  });
}

export function getChatRoles(): Promise<ChatRolesResponse> {
  return requestJson<ChatRolesResponse>("/api/v1/chat/roles", {
    method: "GET",
  });
}

export async function streamChatCompletion(
  payload: ChatCompletionRequest,
  options: {
    signal: AbortSignal;
    onDelta: (content: string) => void;
  },
): Promise<void> {
  const response = await fetch("/api/v1/chat/completions", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
    signal: options.signal,
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(extractErrorMessage(message) || `Request failed with status ${response.status}`);
  }

  if (!response.body) {
    throw new Error("Streaming response is not available");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) {
      break;
    }
    buffer += decoder.decode(value, { stream: true });
    const events = buffer.split("\n\n");
    buffer = events.pop() ?? "";

    for (const event of events) {
      const shouldStop = handleSseEvent(event, options.onDelta);
      if (shouldStop) {
        return;
      }
    }
  }

  if (buffer.trim()) {
    handleSseEvent(buffer, options.onDelta);
  }
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

function handleSseEvent(rawEvent: string, onDelta: (content: string) => void): boolean {
  const dataLines = rawEvent
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => line.startsWith("data:"))
    .map((line) => line.slice("data:".length).trim());

  for (const data of dataLines) {
    if (data === "[DONE]") {
      return true;
    }

    const event = JSON.parse(data) as ChatStreamEvent;
    if (event.type === "delta") {
      onDelta(event.content);
    }
    if (event.type === "error") {
      throw new Error(event.message);
    }
    if (event.type === "done") {
      return false;
    }
  }

  return false;
}

function extractErrorMessage(message: string): string {
  try {
    const payload = JSON.parse(message) as { detail?: string | Array<{ msg?: string }> };
    if (typeof payload.detail === "string") {
      return payload.detail;
    }
    if (Array.isArray(payload.detail)) {
      return payload.detail.map((item) => item.msg).filter(Boolean).join("; ");
    }
    return message;
  } catch {
    return message;
  }
}
