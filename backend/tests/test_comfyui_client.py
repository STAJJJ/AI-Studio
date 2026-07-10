import json
from io import BytesIO
from urllib.parse import parse_qs, urlparse

from app.services.comfyui.client import ComfyUIClient


class MockHTTPResponse:
    def __init__(self, payload: bytes) -> None:
        self._payload = payload

    def __enter__(self) -> "MockHTTPResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def read(self) -> bytes:
        return self._payload


def test_submit_workflow_posts_to_comfyui_prompt_api(monkeypatch) -> None:
    captured = {}

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["timeout"] = timeout
        captured["method"] = request.get_method()
        captured["payload"] = json.loads(request.data.decode("utf-8"))
        return MockHTTPResponse(json.dumps({"prompt_id": "prompt-123"}).encode("utf-8"))

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    client = ComfyUIClient(base_url="http://comfy.local", timeout_seconds=3)
    prompt_id = client.submit_workflow({"1": {"class_type": "SaveImage"}})

    assert prompt_id == "prompt-123"
    assert captured["url"] == "http://comfy.local/prompt"
    assert captured["timeout"] == 3
    assert captured["method"] == "POST"
    assert captured["payload"] == {"prompt": {"1": {"class_type": "SaveImage"}}}


def test_get_history_reads_prompt_history(monkeypatch) -> None:
    def fake_urlopen(request, timeout):
        assert request == "http://comfy.local/history/prompt-123"
        assert timeout == 5
        return MockHTTPResponse(json.dumps({"prompt-123": {"status": {"completed": True}}}).encode("utf-8"))

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    client = ComfyUIClient(base_url="http://comfy.local/", timeout_seconds=5)

    assert client.get_history("prompt-123") == {"prompt-123": {"status": {"completed": True}}}


def test_get_image_reads_binary_image_from_view_api(monkeypatch) -> None:
    def fake_urlopen(request, timeout):
        parsed = urlparse(request)
        assert parsed.path == "/view"
        assert parse_qs(parsed.query) == {
            "filename": ["image.png"],
            "subfolder": ["results"],
            "type": ["output"],
        }
        return MockHTTPResponse(b"png-bytes")

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    client = ComfyUIClient(base_url="http://comfy.local")

    assert client.get_image(filename="image.png", subfolder="results", image_type="output") == b"png-bytes"
