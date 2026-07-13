export type FilePurpose = "source_face" | "target_image" | "target_video" | "output";
export type FaceSwapStatus = "pending" | "running" | "succeeded" | "failed";

export interface FileUploadResponse {
  id: string;
  filename: string;
  content_type: string;
  purpose: FilePurpose;
  size_bytes: number;
}

export interface TaskResult {
  file_id: string;
  download_url: string;
  image_url: string | null;
}

export interface TaskError {
  code: string;
  message: string;
}

export interface FaceSwapTaskResponse {
  id: string;
  task_id: string;
  type: "face_swap" | string;
  status: FaceSwapStatus;
  progress: number;
  message: string;
  created_at: number;
  updated_at: number;
  result: TaskResult | null;
  error: TaskError | null;
}
