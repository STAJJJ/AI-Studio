export interface GenerateImageRequest {
  prompt: string;
  width: number;
  height: number;
}

export interface GenerateImageResponse {
  task_id: string;
  status: "running" | string;
}
