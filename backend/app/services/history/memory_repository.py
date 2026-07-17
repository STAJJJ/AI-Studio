from threading import Lock
from time import time

from app.schemas.history import WorkflowRunCreate, WorkflowRunRecord, WorkflowRunStatus, WorkflowType
from app.services.history.repository import DuplicateWorkflowRunError, WorkflowHistoryRepository, WorkflowRunNotFoundError


class InMemoryWorkflowHistoryRepository(WorkflowHistoryRepository):
    def __init__(self) -> None:
        self._runs: dict[str, WorkflowRunRecord] = {}
        self._external_index: dict[tuple[WorkflowType, str], str] = {}
        self._sequence_by_id: dict[str, int] = {}
        self._next_sequence = 0
        self._lock = Lock()

    def create(self, data: WorkflowRunCreate) -> WorkflowRunRecord:
        key = (data.workflow_type, data.external_task_id)
        with self._lock:
            if key in self._external_index:
                raise DuplicateWorkflowRunError(
                    f"Workflow history already exists for {data.workflow_type}:{data.external_task_id}"
                )
            completed_at = int(time()) if data.status in {WorkflowRunStatus.succeeded, WorkflowRunStatus.failed} else None
            record = WorkflowRunRecord(**data.model_dump(), completed_at=completed_at)
            self._runs[record.id] = record
            self._sequence_by_id[record.id] = self._next_sequence
            self._next_sequence += 1
            self._external_index[key] = record.id
            return record

    def update(self, run_id: str, **changes: object) -> WorkflowRunRecord:
        with self._lock:
            current = self._runs.get(run_id)
            if current is None:
                raise WorkflowRunNotFoundError(f"Workflow history run not found: {run_id}")
            normalized = {key: value for key, value in changes.items() if value is not None}
            status = normalized.get("status")
            if status in {WorkflowRunStatus.succeeded, WorkflowRunStatus.failed} and current.completed_at is None:
                normalized["completed_at"] = int(time())
            updated = current.model_copy(update={**normalized, "updated_at": int(time())})
            self._runs[run_id] = updated
            return updated

    def get(self, run_id: str) -> WorkflowRunRecord:
        with self._lock:
            record = self._runs.get(run_id)
        if record is None:
            raise WorkflowRunNotFoundError(f"Workflow history run not found: {run_id}")
        return record

    def list(
        self,
        *,
        workflow_type: WorkflowType | None = None,
        status: WorkflowRunStatus | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[WorkflowRunRecord], int]:
        with self._lock:
            records = list(self._runs.values())
        if workflow_type is not None:
            records = [record for record in records if record.workflow_type == workflow_type]
        if status is not None:
            records = [record for record in records if record.status == status]
        records.sort(key=lambda record: (record.created_at, self._sequence_by_id.get(record.id, 0)), reverse=True)
        total = len(records)
        return records[offset : offset + limit], total

    def get_by_external_task_id(self, workflow_type: WorkflowType, external_task_id: str) -> WorkflowRunRecord:
        with self._lock:
            run_id = self._external_index.get((workflow_type, external_task_id))
        if run_id is None:
            raise WorkflowRunNotFoundError(f"Workflow history run not found: {workflow_type}:{external_task_id}")
        return self.get(run_id)
