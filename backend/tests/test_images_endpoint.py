from fastapi.testclient import TestClient

from app.api.v1.endpoints import images
from app.main import app
from app.services.image_service import ImageGenerationResponse


client = TestClient(app)


class FakeImageService:
    def __init__(self) -> None:
        self.request = None

    def generate_image(self, request):
        self.request = request
        return ImageGenerationResponse(task_id="prompt-endpoint", status="running")


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
