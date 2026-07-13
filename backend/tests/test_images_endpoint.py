from pathlib import Path

from fastapi.testclient import TestClient

from app.api.v1.endpoints import images
from app.main import app
from app.services.image_service import ImageGenerationResponse, ImageGenerationStatus


client = TestClient(app)


class FakeImageService:
    def __init__(self) -> None:
        self.request = None
        self.task_id = None
        self.result_path = None

    def generate_image(self, request):
        self.request = request
        return ImageGenerationResponse(task_id="prompt-endpoint", status="running")

    def get_generation_status(self, task_id):
        self.task_id = task_id
        return ImageGenerationStatus(
            task_id=task_id,
            status="completed",
            progress=100,
            image_url="/api/v1/images/result/result.png",
        )

    def get_result_path(self, filename):
        assert filename == "result.png"
        assert self.result_path is not None
        return self.result_path


def test_generate_image_endpoint_delegates_to_image_service(monkeypatch) -> None:
    fake_service = FakeImageService()
    monkeypatch.setattr(images, "image_service", fake_service)

    response = client.post(
        "/api/v1/images/generate",
        json={"prompt": "A cinematic portrait", "width": 1024, "height": 1024},
    )

    assert response.status_code == 202
    assert response.json() == {"task_id": "prompt-endpoint", "status": "running"}
    assert fake_service.request.prompt == "A cinematic portrait"
    assert fake_service.request.width == 1024
    assert fake_service.request.height == 1024


def test_get_image_task_status_endpoint_delegates_to_image_service(monkeypatch) -> None:
    fake_service = FakeImageService()
    monkeypatch.setattr(images, "image_service", fake_service)

    response = client.get("/api/v1/images/tasks/prompt-endpoint")

    assert response.status_code == 200
    assert response.json() == {
        "task_id": "prompt-endpoint",
        "status": "completed",
        "progress": 100,
        "image_url": "/api/v1/images/result/result.png",
    }
    assert fake_service.task_id == "prompt-endpoint"


def test_get_image_result_endpoint_returns_png(monkeypatch, tmp_path: Path) -> None:
    result_path = tmp_path / "result.png"
    result_path.write_bytes(b"png-bytes")
    fake_service = FakeImageService()
    fake_service.result_path = result_path
    monkeypatch.setattr(images, "image_service", fake_service)

    response = client.get("/api/v1/images/result/result.png")

    assert response.status_code == 200
    assert response.content == b"png-bytes"
    assert response.headers["content-type"] == "image/png"
