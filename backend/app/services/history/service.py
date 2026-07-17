from app.schemas.history import (
    WorkflowRunCreate,
    WorkflowRunDetailResponse,
    WorkflowRunListResponse,
    WorkflowRunRecord,
    WorkflowRunStatus,
    WorkflowRunSummaryResponse,
    WorkflowType,
)
from app.services.history.memory_repository import InMemoryWorkflowHistoryRepository
from app.services.history.repository import WorkflowHistoryRepository, WorkflowRunNotFoundError


class WorkflowHistoryService:
    def __init__(self, repository: WorkflowHistoryRepository) -> None:
        self._repository = repository

    def create_run(self, data: WorkflowRunCreate) -> WorkflowRunRecord:
        try:
            return self._repository.get_by_external_task_id(data.workflow_type, data.external_task_id)
        except WorkflowRunNotFoundError:
            return self._repository.create(data)

    def update_run(self, run_id: str, **changes: object) -> WorkflowRunRecord:
        return self._repository.update(run_id, **changes)

    def update_by_external_task_id(
        self, workflow_type: WorkflowType, external_task_id: str, **changes: object
    ) -> WorkflowRunRecord:
        run = self._repository.get_by_external_task_id(workflow_type, external_task_id)
        return self.update_run(run.id, **changes)

    def get_run(self, run_id: str) -> WorkflowRunRecord:
        return self._repository.get(run_id)

    def get_by_external_task_id(self, workflow_type: WorkflowType, external_task_id: str) -> WorkflowRunRecord:
        return self._repository.get_by_external_task_id(workflow_type, external_task_id)

    def create_image_generation_run(
        self, *, external_task_id: str, model: str, prompt: str, width: int, height: int
    ) -> WorkflowRunRecord:
        return self.create_run(
            WorkflowRunCreate(
                workflow_type=WorkflowType.image_generation,
                runtime="comfyui",
                provider=model,
                status=WorkflowRunStatus.running,
                progress=0,
                title=self._title_from_text(prompt),
                input_summary=self._summary_from_image_prompt(prompt, width, height),
                input_payload={"model": model, "prompt": prompt, "width": width, "height": height},
                output_payload={},
                external_task_id=external_task_id,
            )
        )

    def create_face_swap_run(self, *, external_task_id: str, source_file_id: str, target_file_id: str) -> WorkflowRunRecord:
        return self.create_run(
            WorkflowRunCreate(
                workflow_type=WorkflowType.face_swap,
                runtime="facefusion",
                provider="facefusion",
                status=WorkflowRunStatus.running,
                progress=0,
                title="Face Swap",
                input_summary=f"{source_file_id} -> {target_file_id}",
                input_payload={"source_file_id": source_file_id, "target_file_id": target_file_id},
                output_payload={},
                external_task_id=external_task_id,
            )
        )

    def list_runs(
        self,
        *,
        workflow_type: WorkflowType | None = None,
        status: WorkflowRunStatus | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> WorkflowRunListResponse:
        records, total = self._repository.list(workflow_type=workflow_type, status=status, limit=limit, offset=offset)
        return WorkflowRunListResponse(
            items=[self.to_summary_response(record) for record in records],
            total=total,
            limit=limit,
            offset=offset,
        )

    def to_summary_response(self, record: WorkflowRunRecord) -> WorkflowRunSummaryResponse:
        return WorkflowRunSummaryResponse(
            id=record.id,
            workflow_type=record.workflow_type,
            runtime=record.runtime,
            provider=record.provider,
            status=record.status,
            progress=record.progress,
            title=record.title,
            input_summary=record.input_summary,
            result_url=self._result_url(record),
            external_task_id=record.external_task_id,
            created_at=record.created_at,
            updated_at=record.updated_at,
            completed_at=record.completed_at,
        )

    def to_detail_response(self, record: WorkflowRunRecord) -> WorkflowRunDetailResponse:
        summary = self.to_summary_response(record)
        return WorkflowRunDetailResponse(
            **summary.model_dump(),
            input_payload=record.input_payload,
            output_payload=record.output_payload,
            result_file_id=record.result_file_id,
            error_code=record.error_code,
            error_message=record.error_message,
        )

    def _result_url(self, record: WorkflowRunRecord) -> str | None:
        if record.result_file_id is None:
            return None
        return f"/api/v1/history/{record.id}/result"

    def _title_from_text(self, value: str, limit: int = 80) -> str:
        compact = " ".join(value.split())
        return compact[:limit] if compact else "Untitled"

    def _summary_from_image_prompt(self, prompt: str, width: int, height: int) -> str:
        return f"{self._title_from_text(prompt, 120)} ({width}x{height})"


workflow_history_service = WorkflowHistoryService(InMemoryWorkflowHistoryRepository())
