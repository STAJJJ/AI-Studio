import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
import urllib.request
from urllib.request import Request


class ComfyUIClientError(RuntimeError):
    """Raised when ComfyUI HTTP API communication fails."""


class ComfyUIClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8188", timeout_seconds: int = 30) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds

    def submit_workflow(self, workflow: dict[str, Any]) -> str:
        payload = {"prompt": workflow}
        response = self._post_json("/prompt", payload)
        prompt_id = response.get("prompt_id")
        if not isinstance(prompt_id, str) or not prompt_id:
            raise ComfyUIClientError("ComfyUI response did not include prompt_id")
        return prompt_id

    def get_history(self, prompt_id: str) -> dict[str, Any]:
        return self._get_json(f"/history/{prompt_id}")

    def get_image(self, filename: str, subfolder: str = "", image_type: str = "output") -> bytes:
        query = urlencode({"filename": filename, "subfolder": subfolder, "type": image_type})
        return self._get_bytes(f"/view?{query}")

    def _post_json(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        data = json.dumps(payload).encode("utf-8")
        request = Request(
            self._build_url(path),
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        return self._read_json(request)

    def _get_json(self, path: str) -> dict[str, Any]:
        return self._read_json(self._build_url(path))

    def _get_bytes(self, path: str) -> bytes:
        try:
            with urllib.request.urlopen(self._build_url(path), timeout=self._timeout_seconds) as response:
                return response.read()
        except (HTTPError, URLError, TimeoutError) as exc:
            raise ComfyUIClientError(f"ComfyUI image request failed: {exc}") from exc

    def _read_json(self, request: Request | str) -> dict[str, Any]:
        try:
            with urllib.request.urlopen(request, timeout=self._timeout_seconds) as response:
                payload = response.read()
        except (HTTPError, URLError, TimeoutError) as exc:
            raise ComfyUIClientError(f"ComfyUI request failed: {exc}") from exc
        try:
            data = json.loads(payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ComfyUIClientError("ComfyUI returned invalid JSON") from exc
        if not isinstance(data, dict):
            raise ComfyUIClientError("ComfyUI returned unexpected JSON payload")
        return data

    def _build_url(self, path: str) -> str:
        if not path.startswith("/"):
            path = f"/{path}"
        return f"{self._base_url}{path}"
