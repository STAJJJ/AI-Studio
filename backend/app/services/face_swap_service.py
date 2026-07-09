from threading import Thread

from app.executors.base import BaseExecutor
from app.executors.mock_executor import mock_executor
from app.schemas.file import FilePurpose
from app.schemas.task import FaceSwapTaskCreateRequest, TaskRecord, TaskResponse
from app.services.files.file_service import FileService, file_service
from app.services.jobs.task_manager import TaskManager, task_manager


class FaceSwapService:
    def __init__(self, files: FileService, tasks: TaskManager, executor: BaseExecutor) -> None:
        self._files = files
        self._tasks = tasks
        self._executor = executor

    def create_task(self, request: FaceSwapTaskCreateRequest) -> TaskResponse:
        self._validate_input_files(request)
        task = self._tasks.create_task(
            task_type="face_swap",
            payload={
                "source_file_id": request.source_file_id,
                "target_file_id": request.target_file_id,
                "options": request.options,
            },
        )
        Thread(target=self._run_task, args=(task,), daemon=True).start()
        return TaskResponse.from_record(task)

    def _run_task(self, task: TaskRecord) -> None:
        try:
            self._tasks.mark_running(task.id, message="Mock AI processing")
            result_file_id = self._executor.execute(task)
            self._tasks.mark_succeeded(task.id, result_file_id=result_file_id)
        except Exception as exc:  # noqa: BLE001 - domain boundary records executor failures.
            self._tasks.mark_failed(task.id, code="MOCK_EXECUTOR_FAILED", message=str(exc))

    def _validate_input_files(self, request: FaceSwapTaskCreateRequest) -> None:
        source = self._files.get_file(request.source_file_id)
        target = self._files.get_file(request.target_file_id)
        if source.purpose != FilePurpose.source_face:
            raise ValueError("source_file_id must reference a source_face file")
        if target.purpose not in {FilePurpose.target_image, FilePurpose.target_video}:
            raise ValueError("target_file_id must reference a target file")


face_swap_service = FaceSwapService(file_service, task_manager, mock_executor)
