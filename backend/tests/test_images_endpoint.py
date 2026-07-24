from fastapi.testclient import TestClient

from app.api.v1.endpoints import images
from app.main import app
from app.services.comfyui.model_registry import UnknownImageModelError
from app.services.comfyui.client import ComfyUIImage, ComfyUIImageNotFoundError, ComfyUIUnavailableError
from app.services.image_service import ImageCheckpointNotFoundError, ImageGenerationResponse, ImageGenerationStatus


client = TestClient(app)


class FakeImageService:
    def __init__(self) -> None:
        self.request = None
        self.task_id = None

    def generate_image(self, request):
        self.request = request
        if request.model in {"unknown", "flux"}:
            raise UnknownImageModelError(f"Unsupported image model: {request.model}")
        return ImageGenerationResponse(task_id="prompt-endpoint", status="running")

    def get_generation_status(self, task_id):
        self.task_id = task_id
        return ImageGenerationStatus(
            task_id=task_id,
            status="completed",
            progress=100,
            image_url="/api/v1/images/result/result.png",
        )

    def get_result_image(self, filename):
        assert filename == "result.png"
        return ComfyUIImage(content=b"png-bytes", content_type="image/png", filename=filename)


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
    assert fake_service.request.model is None
    assert fake_service.request.width == 1024
    assert fake_service.request.height == 1024


def test_generate_image_endpoint_accepts_model(monkeypatch) -> None:
    fake_service = FakeImageService()
    monkeypatch.setattr(images, "image_service", fake_service)

    response = client.post(
        "/api/v1/images/generate",
        json={"prompt": "A forest cabin", "model": "sd15"},
    )

    assert response.status_code == 202
    assert fake_service.request.prompt == "A forest cabin"
    assert fake_service.request.model == "sd15"
    assert fake_service.request.width is None
    assert fake_service.request.height is None


def test_generate_image_endpoint_rejects_unknown_model(monkeypatch) -> None:
    fake_service = FakeImageService()
    monkeypatch.setattr(images, "image_service", fake_service)

    response = client.post(
        "/api/v1/images/generate",
        json={"prompt": "A forest cabin", "model": "unknown"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Unsupported image model: unknown"


def test_generate_image_endpoint_rejects_removed_flux_model(monkeypatch) -> None:
    fake_service = FakeImageService()
    monkeypatch.setattr(images, "image_service", fake_service)

    response = client.post("/api/v1/images/generate", json={"prompt": "A forest cabin", "model": "flux"})

    assert response.status_code == 400


def test_generate_image_endpoint_returns_503_when_comfyui_is_unavailable(monkeypatch) -> None:
    class UnavailableImageService(FakeImageService):
        def generate_image(self, request):
            raise ComfyUIUnavailableError("ComfyUI is unavailable at http://127.0.0.1:8188")

    monkeypatch.setattr(images, "image_service", UnavailableImageService())

    response = client.post("/api/v1/images/generate", json={"prompt": "A forest cabin", "model": "sd15"})

    assert response.status_code == 503
    assert "unavailable" in response.json()["detail"].lower()


def test_generate_image_endpoint_reports_missing_checkpoint(monkeypatch) -> None:
    class MissingCheckpointService(FakeImageService):
        def generate_image(self, request):
            raise ImageCheckpointNotFoundError("ComfyUI checkpoint is not installed: missing.safetensors")

    monkeypatch.setattr(images, "image_service", MissingCheckpointService())

    response = client.post("/api/v1/images/generate", json={"prompt": "A forest cabin", "model": "sd15"})

    assert response.status_code == 422
    assert "missing.safetensors" in response.json()["detail"]


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


def test_get_image_task_status_returns_503_when_comfyui_is_unavailable(monkeypatch) -> None:
    class UnavailableImageService(FakeImageService):
        def get_generation_status(self, task_id):
            raise ComfyUIUnavailableError("ComfyUI is unavailable at http://127.0.0.1:8188")

    monkeypatch.setattr(images, "image_service", UnavailableImageService())

    response = client.get("/api/v1/images/tasks/prompt-endpoint")

    assert response.status_code == 503


def test_get_image_result_endpoint_proxies_png_with_download_filename(monkeypatch) -> None:
    fake_service = FakeImageService()
    monkeypatch.setattr(images, "image_service", fake_service)

    response = client.get("/api/v1/images/result/result.png")

    assert response.status_code == 200
    assert response.content == b"png-bytes"
    assert response.headers["content-type"] == "image/png"
    assert "result.png" in response.headers["content-disposition"]


def test_get_image_result_endpoint_maps_comfyui_404(monkeypatch) -> None:
    class MissingImageService(FakeImageService):
        def get_result_image(self, filename):
            raise ComfyUIImageNotFoundError("ComfyUI image not found: result.png")

    monkeypatch.setattr(images, "image_service", MissingImageService())

    response = client.get("/api/v1/images/result/result.png")

    assert response.status_code == 404
