import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.executors.facefusion_executor import ExecutionResult
from app.schemas.history import WorkflowRunStatus, WorkflowType
from app.main import app
from app.services.face_swap_service import face_swap_service
from app.services.files.file_service import FileServiceError, file_service


client = TestClient(app)


class FakeFaceFusionExecutor:
    def __init__(self, exit_code: int = 0, write_output: bool = True) -> None:
        self.exit_code = exit_code
        self.write_output = write_output
        self.calls = []

    def execute(self, source_path: Path, target_path: Path, output_path: Path) -> ExecutionResult:
        self.calls.append((source_path, target_path, output_path))
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if self.write_output:
            output_path.write_bytes(
                bytes.fromhex(
                    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
                    "0000000a49444154789c6360000002000100ffff03000006000557bfab0d00000000"
                    "49454e44ae426082"
                )
            )
        return ExecutionResult(
            command=["python", "facefusion.py", "headless-run"],
            stdout="fake stdout",
            stderr="fake stderr" if self.exit_code else "",
            exit_code=self.exit_code,
            duration_seconds=0.25,
            output_path=output_path,
        )


def upload_test_file(
    filename: str = "source.png",
    content_type: str = "image/png",
    purpose: str = "source_face",
) -> str:
    response = client.post(
        "/api/v1/files",
        data={"purpose": purpose},
        files={"file": (filename, b"fake image bytes", content_type)},
    )
    assert response.status_code == 201
    return response.json()["id"]


def wait_for_terminal_task(task_id: str) -> dict:
    final_payload = None
    for _ in range(40):
        status_response = client.get(f"/api/v1/tasks/{task_id}")
        assert status_response.status_code == 200
        final_payload = status_response.json()
        if final_payload["status"] in {"succeeded", "failed"}:
            return final_payload
        time.sleep(0.1)
    raise AssertionError(f"Task did not finish: {final_payload}")


def test_file_upload_get_and_delete() -> None:
    file_id = upload_test_file()

    get_response = client.get(f"/api/v1/files/{file_id}")
    assert get_response.status_code == 200
    payload = get_response.json()
    assert payload["id"] == file_id
    assert payload["filename"] == "source.png"
    assert payload["content_type"] == "image/png"
    assert payload["purpose"] == "source_face"
    assert payload["size_bytes"] > 0

    delete_response = client.delete(f"/api/v1/files/{file_id}")
    assert delete_response.status_code == 204

    missing_response = client.get(f"/api/v1/files/{file_id}")
    assert missing_response.status_code == 404


def test_file_upload_rejects_unsupported_mime_type() -> None:
    response = client.post(
        "/api/v1/files",
        data={"purpose": "source_face"},
        files={"file": ("source.txt", b"not an image", "text/plain")},
    )

    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]


def test_face_swap_task_lifecycle_and_result(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_executor = FakeFaceFusionExecutor()
    monkeypatch.setattr(face_swap_service, "_executor", fake_executor)

    source_file_id = upload_test_file("source.png", "image/png", "source_face")
    target_file_id = upload_test_file("target.png", "image/png", "target_image")

    create_response = client.post(
        "/api/v1/face-swap/tasks",
        json={"source_file_id": source_file_id, "target_file_id": target_file_id},
    )

    assert create_response.status_code == 201
    task_payload = create_response.json()
    task_id = task_payload["task_id"]
    assert task_payload["id"] == task_id
    assert task_payload["status"] in {"pending", "running"}
    assert task_payload["type"] == "face_swap"

    final_payload = wait_for_terminal_task(task_id)

    assert final_payload["status"] == "succeeded"
    assert final_payload["progress"] == 100
    assert final_payload["result"] is not None
    assert final_payload["result"]["image_url"] == f"/api/v1/tasks/{task_id}/result"
    assert fake_executor.calls
    assert fake_executor.calls[0][2].name == "result.png"
    assert fake_executor.calls[0][2].parent.name == task_id

    result_response = client.get(f"/api/v1/tasks/{task_id}/result")
    assert result_response.status_code == 200
    assert result_response.content
    assert result_response.headers["content-type"] == "image/png"


def test_face_swap_output_extension_matches_jpeg_target(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_executor = FakeFaceFusionExecutor()
    monkeypatch.setattr(face_swap_service, "_executor", fake_executor)

    source_file_id = upload_test_file("source.jpg", "image/jpeg", "source_face")
    target_file_id = upload_test_file("target.jpg", "image/jpeg", "target_image")

    create_response = client.post(
        "/api/v1/face-swap/tasks",
        json={"source_file_id": source_file_id, "target_file_id": target_file_id},
    )

    assert create_response.status_code == 201
    task_id = create_response.json()["task_id"]
    final_payload = wait_for_terminal_task(task_id)

    assert final_payload["status"] == "succeeded"
    assert fake_executor.calls[0][2].name == "result.jpg"
    assert final_payload["result"] is not None


def test_face_swap_rejects_target_video_for_first_demo() -> None:
    source_file_id = upload_test_file("source.png", "image/png", "source_face")
    target_file_id = upload_test_file("target.png", "image/png", "target_video")

    response = client.post(
        "/api/v1/face-swap/tasks",
        json={"source_file_id": source_file_id, "target_file_id": target_file_id},
    )

    assert response.status_code == 400
    assert "target_image" in response.json()["detail"]


def test_face_swap_failure_maps_to_failed_task(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(face_swap_service, "_executor", FakeFaceFusionExecutor(exit_code=1, write_output=False))
    source_file_id = upload_test_file("source.png", "image/png", "source_face")
    target_file_id = upload_test_file("target.png", "image/png", "target_image")

    create_response = client.post(
        "/api/v1/face-swap/tasks",
        json={"source_file_id": source_file_id, "target_file_id": target_file_id},
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["task_id"]

    final_payload = wait_for_terminal_task(task_id)

    assert final_payload["status"] == "failed"
    assert final_payload["error"] is not None
    assert final_payload["error"]["code"] == "FACEFUSION_EXECUTION_FAILED"

    result_response = client.get(f"/api/v1/tasks/{task_id}/result")
    assert result_response.status_code == 409
    assert "FaceFusion failed" in result_response.json()["detail"]


def test_task_result_endpoint_rejects_non_face_swap_task() -> None:
    from app.services.jobs.task_manager import task_manager

    task = task_manager.create_task(task_type="other", payload={})

    response = client.get(f"/api/v1/tasks/{task.id}/result")

    assert response.status_code == 400
    assert "face_swap" in response.json()["detail"]


def test_task_output_registration_rejects_path_outside_output_dir(tmp_path: Path) -> None:
    outside_path = tmp_path / "result.png"
    outside_path.write_bytes(b"png")

    with pytest.raises(FileServiceError):
        file_service.register_task_output_file("task_bad", outside_path)


def test_face_swap_creates_and_updates_history_on_success(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_executor = FakeFaceFusionExecutor()
    monkeypatch.setattr(face_swap_service, "_executor", fake_executor)
    source_file_id = upload_test_file("source.png", "image/png", "source_face")
    target_file_id = upload_test_file("target.png", "image/png", "target_image")

    create_response = client.post(
        "/api/v1/face-swap/tasks",
        json={"source_file_id": source_file_id, "target_file_id": target_file_id},
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["task_id"]
    final_payload = wait_for_terminal_task(task_id)

    run = face_swap_service._history.get_by_external_task_id(WorkflowType.face_swap, task_id)
    assert final_payload["status"] == "succeeded"
    assert run.status == WorkflowRunStatus.succeeded
    assert run.input_payload == {"source_file_id": source_file_id, "target_file_id": target_file_id}
    assert run.result_file_id == final_payload["result"]["file_id"]
    assert "/Users/" not in str(run.model_dump())
    assert "/3241903007/" not in str(run.model_dump())


def test_face_swap_updates_history_on_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(face_swap_service, "_executor", FakeFaceFusionExecutor(exit_code=1, write_output=False))
    source_file_id = upload_test_file("source.png", "image/png", "source_face")
    target_file_id = upload_test_file("target.png", "image/png", "target_image")

    create_response = client.post(
        "/api/v1/face-swap/tasks",
        json={"source_file_id": source_file_id, "target_file_id": target_file_id},
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["task_id"]
    final_payload = wait_for_terminal_task(task_id)

    run = face_swap_service._history.get_by_external_task_id(WorkflowType.face_swap, task_id)
    assert final_payload["status"] == "failed"
    assert run.status == WorkflowRunStatus.failed
    assert run.error_code == "FACEFUSION_EXECUTION_FAILED"
    assert run.error_message
    assert run.completed_at is not None
