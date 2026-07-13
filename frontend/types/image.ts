export type ImageGenerationStatusValue = "running" | "completed" | "failed";

export interface GenerateImageRequest {
  prompt: string;
  width: number;
  height: number;
}

export interface GenerateImageResponse {
  task_id: string;
  status: ImageGenerationStatusValue | string;
}

export interface ImageGenerationStatusResponse {
  task_id: string;
  status: ImageGenerationStatusValue;
  progress: number;
  image_url: string | null;
}
