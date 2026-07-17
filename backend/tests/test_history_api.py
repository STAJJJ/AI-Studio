from fastapi.testclient import TestClient
from uuid import uuid4

from app.main import app
from app.schemas.history import WorkflowRunCreate, WorkflowRunStatus, WorkflowType
from app.services.history.service import workflow_history_service

client = TestClient(app)


def create_history_run(title: str = "History Item", workflow_type: WorkflowType = WorkflowType.image_generation):
    return workflow_history_service.create_run(
        WorkflowRunCreate(
            workflow_type=workflow_type,
            runtime="comfyui" if workflow_type == WorkflowType.image_generation else "facefusion",
            provider="sd15" if workflow_type == WorkflowType.image_generation else "facefusion",
            status=WorkflowRunStatus.succeeded,
            progress=100,
            title=title,
            input_summary="summary",
            input_payload={"prompt": "summary"} if workflow_type == WorkflowType.image_generation else {"source_file_id": "file_a", "target_file_id": "file_b"},
            output_payload={"filename": "result.png"},
            result_file_id="file_result",
            external_task_id=f"external_{title}_{uuid4().hex}",
        )
    )


def test_history_list_endpoint_returns_summary_and_dynamic_result_url() -> None:
    run = create_history_run("List Item")

    response = client.get("/api/v1/history?limit=100")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] >= 1
    item = next(item for item in payload["items"] if item["id"] == run.id)
    assert item["title"] == "List Item"
    assert item["result_url"] == f"/api/v1/history/{run.id}/result"
    assert "input_payload" not in item


def test_history_detail_endpoint_returns_full_payload_without_absolute_paths() -> None:
    run = create_history_run("Detail Item")

    response = client.get(f"/api/v1/history/{run.id}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == run.id
    assert payload["input_payload"] == {"prompt": "summary"}
    serialized = response.text
    assert "/Users/" not in serialized
    assert "/3241903007/" not in serialized


def test_history_endpoint_filters_and_validates_params() -> None:
    create_history_run("Image Filter", WorkflowType.image_generation)
    create_history_run("Face Filter", WorkflowType.face_swap)

    filtered = client.get("/api/v1/history?workflow_type=face_swap&status=succeeded&limit=1&offset=0")
    invalid = client.get("/api/v1/history?workflow_type=chat")

    assert filtered.status_code == 200
    assert filtered.json()["items"][0]["workflow_type"] == "face_swap"
    assert invalid.status_code == 422


def test_history_detail_endpoint_returns_404_for_missing_run() -> None:
    response = client.get("/api/v1/history/run_missing")

    assert response.status_code == 404
