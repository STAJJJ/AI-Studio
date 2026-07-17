from abc import ABC, abstractmethod

from app.schemas.history import WorkflowRunCreate, WorkflowRunRecord, WorkflowRunStatus, WorkflowRunUpdate, WorkflowType


class WorkflowRunNotFoundError(ValueError):
    pass


class DuplicateWorkflowRunError(ValueError):
    pass


class WorkflowHistoryRepository(ABC):
    @abstractmethod
    def create(self, data: WorkflowRunCreate) -> WorkflowRunRecord:
        raise NotImplementedError

    @abstractmethod
    def update(self, run_id: str, **changes: object) -> WorkflowRunRecord:
        raise NotImplementedError

    @abstractmethod
    def get(self, run_id: str) -> WorkflowRunRecord:
        raise NotImplementedError

    @abstractmethod
    def list(
        self,
        *,
        workflow_type: WorkflowType | None = None,
        status: WorkflowRunStatus | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[WorkflowRunRecord], int]:
        raise NotImplementedError

    @abstractmethod
    def get_by_external_task_id(self, workflow_type: WorkflowType, external_task_id: str) -> WorkflowRunRecord:
        raise NotImplementedError
