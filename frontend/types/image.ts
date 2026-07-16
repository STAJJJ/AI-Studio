export type ImageGenerationStatusValue = "pending" | "running" | "completed" | "failed";

export interface GenerateImageRequest {
  prompt: string;
  model?: string;
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

export interface RuntimeModel {
  id: string;
  name: string;
  width: number;
  height: number;
}

export interface RuntimeResponse {
  current_model: string;
  current_model_id: string;
  engine: string;
  backend: string;
  gpu: string;
  status: string;
  models: RuntimeModel[];
}
