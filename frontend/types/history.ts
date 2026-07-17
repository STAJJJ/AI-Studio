export type WorkflowType = "image_generation" | "face_swap";
export type WorkflowRunStatus = "pending" | "running" | "succeeded" | "failed";

export interface WorkflowRunSummary {
  id: string;
  workflow_type: WorkflowType;
  runtime: string;
  provider: string;
  status: WorkflowRunStatus;
  progress: number;
  title: string;
  input_summary: string;
  result_url: string | null;
  external_task_id: string;
  created_at: number;
  updated_at: number;
  completed_at: number | null;
}

export interface WorkflowRunDetail extends WorkflowRunSummary {
  input_payload: Record<string, unknown>;
  output_payload: Record<string, unknown>;
  result_file_id: string | null;
  error_code: string | null;
  error_message: string | null;
}

export interface WorkflowHistoryListResponse {
  items: WorkflowRunSummary[];
  total: number;
  limit: number;
  offset: number;
}

export interface HistoryFilters {
  workflowType: WorkflowType | "all";
  status: WorkflowRunStatus | "all";
}
