import time
from pathlib import Path

from app.core.config import Settings, get_settings
from app.executors.base import BaseExecutor
from app.schemas.task import TaskRecord
from app.services.files.file_service import FileService, file_service


class MockExecutor(BaseExecutor):
    def __init__(self, settings: Settings, files: FileService) -> None:
        self._settings = settings
        self._files = files

    def execute(self, task: TaskRecord) -> str:
        time.sleep(self._settings.mock_executor_delay_seconds)
        placeholder = self._create_placeholder_output(task.id)
        metadata = self._files.register_output_file(placeholder, filename=f"{task.id}.png", content_type="image/png")
        placeholder.unlink(missing_ok=True)
        return metadata.id

    def _create_placeholder_output(self, task_id: str) -> Path:
        temp_path = self._settings.output_dir / f"{task_id}_mock.png"
        temp_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path.write_bytes(
            bytes.fromhex(
                "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
                "0000000a49444154789c6360000002000100ffff03000006000557bfab0d00000000"
                "49454e44ae426082"
            )
        )
        return temp_path


mock_executor = MockExecutor(get_settings(), file_service)
