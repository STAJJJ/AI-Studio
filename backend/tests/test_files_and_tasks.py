import time

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def upload_test_file(filename: str = "source.png", content_type: str = "image/png") -> str:
    response = client.post(
        "/api/v1/files",
        data={"purpose": "source_face"},
        files={"file": (filename, b"fake image bytes", content_type)},
    )
    assert response.status_code == 201
    return response.json()["id"]


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


def test_face_swap_task_lifecycle_and_result() -> None:
    source_file_id = upload_test_file("source.png", "image/png")
    target_response = client.post(
        "/api/v1/files",
        data={"purpose": "target_image"},
        files={"file": ("target.png", b"fake target bytes", "image/png")},
    )
    assert target_response.status_code == 201
    target_file_id = target_response.json()["id"]

    create_response = client.post(
        "/api/v1/face-swap/tasks",
        json={
            "source_file_id": source_file_id,
            "target_file_id": target_file_id,
            "options": {"executor": "mock"},
        },
    )

    assert create_response.status_code == 201
    task_payload = create_response.json()
    task_id = task_payload["id"]
    assert task_payload["status"] in {"pending", "running"}
    assert task_payload["type"] == "face_swap"

    final_payload = None
    for _ in range(40):
        status_response = client.get(f"/api/v1/tasks/{task_id}")
        assert status_response.status_code == 200
        final_payload = status_response.json()
        if final_payload["status"] == "succeeded":
            break
        time.sleep(0.1)

    assert final_payload is not None
    assert final_payload["status"] == "succeeded"
    assert final_payload["progress"] == 100
    assert final_payload["result"] is not None

    result_response = client.get(f"/api/v1/tasks/{task_id}/result")
    assert result_response.status_code == 200
    assert result_response.content
    assert result_response.headers["content-type"] == "image/png"
