from threading import Lock
from time import time
from typing import Any

from app.schemas.task import TaskError, TaskRecord, TaskResult, TaskStatus


class TaskNotFoundError(ValueError):
    pass


class TaskResultNotReadyError(ValueError):
    pass


class TaskManager:
    def __init__(self) -> None:
        self._tasks: dict[str, TaskRecord] = {}
        self._lock = Lock()

    def create_task(self, task_type: str, payload: dict) -> TaskRecord:
        task = TaskRecord(type=task_type, payload=payload)
        with self._lock:
            self._tasks[task.id] = task
        return task

    def get_task(self, task_id: str) -> TaskRecord:
        with self._lock:
            task = self._tasks.get(task_id)
        if task is None:
            raise TaskNotFoundError(f"Task not found: {task_id}")
        return task

    def mark_running(self, task_id: str, message: str = "Running") -> TaskRecord:
        return self._update(task_id, status=TaskStatus.running, progress=10, message=message)

    def mark_succeeded(self, task_id: str, result_file_id: str) -> TaskRecord:
        download_url = f"/api/v1/tasks/{task_id}/result"
        return self._update(
            task_id,
            status=TaskStatus.succeeded,
            progress=100,
            message="Completed",
            result=TaskResult(file_id=result_file_id, download_url=download_url, image_url=download_url),
            error=None,
        )

    def mark_failed(self, task_id: str, code: str, message: str) -> TaskRecord:
        return self._update(
            task_id,
            status=TaskStatus.failed,
            progress=100,
            message="Failed",
            error=TaskError(code=code, message=message),
        )

    def merge_payload(self, task_id: str, values: dict[str, Any]) -> TaskRecord:
        task = self.get_task(task_id)
        return self._update(task_id, payload={**task.payload, **values})

    def require_result(self, task_id: str) -> TaskRecord:
        task = self.get_task(task_id)
        if task.status != TaskStatus.succeeded or task.result is None:
            raise TaskResultNotReadyError(f"Task result is not ready: {task_id}")
        return task

    def _update(self, task_id: str, **changes: object) -> TaskRecord:
        with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                raise TaskNotFoundError(f"Task not found: {task_id}")
            updated = task.model_copy(update={**changes, "updated_at": int(time())})
            self._tasks[task_id] = updated
            return updated


task_manager = TaskManager()
