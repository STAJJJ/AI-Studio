from pathlib import Path
from threading import Thread
from typing import Protocol

from app.core.config import Settings, get_settings
from app.executors.facefusion_executor import ExecutionResult, FaceFusionExecutor
from app.schemas.file import FileMetadata, FilePurpose
from app.schemas.task import FaceSwapTaskCreateRequest, TaskRecord, TaskResponse
from app.services.files.file_service import FileService, file_service
from app.services.jobs.task_manager import TaskManager, task_manager


class FaceSwapExecutionError(RuntimeError):
    pass


class FaceSwapExecutorProtocol(Protocol):
    def execute(self, source_path: Path, target_path: Path, output_path: Path) -> ExecutionResult:
        ...


class FaceSwapService:
    def __init__(self, files: FileService, tasks: TaskManager, executor: FaceSwapExecutorProtocol) -> None:
        self._files = files
        self._tasks = tasks
        self._executor = executor

    def create_task(self, request: FaceSwapTaskCreateRequest) -> TaskResponse:
        source, target = self._validate_input_files(request)
        task = self._tasks.create_task(
            task_type="face_swap",
            payload={
                "source_file_id": request.source_file_id,
                "target_file_id": request.target_file_id,
                "source_path": str(source.path),
                "target_path": str(target.path),
                "options": request.options,
            },
        )
        Thread(target=self._run_task, args=(task,), daemon=True).start()
        return TaskResponse.from_record(task)

    def _run_task(self, task: TaskRecord) -> None:
        output_path = self._build_output_path(task.id)
        try:
            self._tasks.mark_running(task.id, message="Running FaceFusion")
            source_path = Path(str(task.payload["source_path"]))
            target_path = Path(str(task.payload["target_path"]))
            result = self._executor.execute(source_path=source_path, target_path=target_path, output_path=output_path)
            self._tasks.merge_payload(task.id, {"execution": self._execution_payload(result)})

            if result.exit_code != 0:
                raise FaceSwapExecutionError(self._summarize_failure(result))
            if not result.output_path.exists() or result.output_path.stat().st_size == 0:
                raise FaceSwapExecutionError("FaceFusion completed without a valid output image")

            metadata = self._files.register_task_output_file(task.id, result.output_path, content_type="image/png")
            self._tasks.merge_payload(
                task.id,
                {
                    "result_file": {
                        "file_id": metadata.id,
                        "filename": metadata.filename,
                        "content_type": metadata.content_type,
                        "size_bytes": metadata.size_bytes,
                        "path": str(metadata.path),
                    }
                },
            )
            self._tasks.mark_succeeded(task.id, result_file_id=metadata.id)
        except Exception as exc:  # noqa: BLE001 - background task boundary must persist failures.
            self._tasks.mark_failed(task.id, code="FACEFUSION_EXECUTION_FAILED", message=str(exc))

    def _validate_input_files(self, request: FaceSwapTaskCreateRequest) -> tuple[FileMetadata, FileMetadata]:
        source = self._files.get_file(request.source_file_id)
        target = self._files.get_file(request.target_file_id)
        if source.purpose != FilePurpose.source_face:
            raise ValueError("source_file_id must reference a source_face file")
        if target.purpose != FilePurpose.target_image:
            raise ValueError("target_file_id must reference a target_image file")
        if not source.content_type.startswith("image/"):
            raise ValueError("source_file_id must reference an image file")
        if not target.content_type.startswith("image/"):
            raise ValueError("target_file_id must reference an image file")
        if not source.path.is_file():
            raise ValueError("source file does not exist on disk")
        if not target.path.is_file():
            raise ValueError("target file does not exist on disk")
        return source, target

    def _build_output_path(self, task_id: str) -> Path:
        safe_task_id = Path(task_id).name
        return self._files.output_dir / safe_task_id / "result.png"

    def _execution_payload(self, result: ExecutionResult) -> dict[str, object]:
        return {
            "duration_seconds": round(result.duration_seconds, 3),
            "exit_code": result.exit_code,
            "stdout_summary": self._summarize_text(result.stdout),
            "stderr_summary": self._summarize_text(result.stderr),
            "output_path": str(result.output_path),
        }

    def _summarize_failure(self, result: ExecutionResult) -> str:
        stderr = self._summarize_text(result.stderr)
        stdout = self._summarize_text(result.stdout)
        detail = stderr or stdout or "FaceFusion exited with a non-zero status"
        return f"FaceFusion failed with exit code {result.exit_code}: {detail}"

    def _summarize_text(self, value: str, limit: int = 1200) -> str:
        normalized = "\n".join(line.strip() for line in value.splitlines() if line.strip())
        return normalized[-limit:]


def build_facefusion_executor(settings: Settings) -> FaceFusionExecutor:
    return FaceFusionExecutor(
        facefusion_root=settings.facefusion_project_path,
        python_executable=settings.facefusion_python_path,
        timeout_seconds=settings.facefusion_timeout_seconds,
        execution_provider=settings.facefusion_execution_provider,
        execution_device_ids=[settings.facefusion_device_id],
    )


_settings = get_settings()
face_swap_service = FaceSwapService(file_service, task_manager, build_facefusion_executor(_settings))
