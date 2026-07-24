from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_runtime_endpoint_returns_current_image_model() -> None:
    response = client.get("/api/v1/runtime")

    assert response.status_code == 200
    assert response.json() == {
        "current_model": "Stable Diffusion 1.5",
        "current_model_id": "sd15",
        "engine": "ComfyUI",
        "backend": "FastAPI",
        "gpu": "Apple Silicon MPS",
        "status": "Ready",
        "models": [
            {
                "id": "sd15",
                "name": "Stable Diffusion 1.5",
                "width": 512,
                "height": 512,
            },
            {
                "id": "sdxl-lightning-4step",
                "name": "SDXL Lightning 4-Step",
                "width": 768,
                "height": 768,
            },
        ],
    }
