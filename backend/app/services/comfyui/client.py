import json
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
import urllib.request
from urllib.request import Request


class ComfyUIClientError(RuntimeError):
    """Raised when ComfyUI HTTP API communication fails."""


class ComfyUIUnavailableError(ComfyUIClientError):
    """Raised when the configured ComfyUI service cannot be reached."""


class ComfyUIImageNotFoundError(ComfyUIClientError):
    """Raised when ComfyUI no longer has the requested output image."""


@dataclass(frozen=True)
class ComfyUIImage:
    content: bytes
    content_type: str
    filename: str


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

    def list_checkpoints(self) -> set[str]:
        payload = self._get_json("/object_info/CheckpointLoaderSimple")
        try:
            options = payload["CheckpointLoaderSimple"]["input"]["required"]["ckpt_name"][0]
        except (KeyError, IndexError, TypeError) as exc:
            raise ComfyUIClientError("ComfyUI returned invalid checkpoint metadata") from exc
        if not isinstance(options, list) or not all(isinstance(item, str) for item in options):
            raise ComfyUIClientError("ComfyUI returned invalid checkpoint metadata")
        return set(options)

    def get_image(self, filename: str, subfolder: str = "", image_type: str = "output") -> ComfyUIImage:
        query = urlencode({"filename": filename, "subfolder": subfolder, "type": image_type})
        request_url = self._build_url(f"/view?{query}")
        try:
            with urllib.request.urlopen(request_url, timeout=self._timeout_seconds) as response:
                content_type = response.headers.get("Content-Type", "application/octet-stream").split(";", 1)[0]
                return ComfyUIImage(content=response.read(), content_type=content_type, filename=filename)
        except HTTPError as exc:
            if exc.code == 404:
                raise ComfyUIImageNotFoundError(f"ComfyUI image not found: {filename}") from exc
            raise ComfyUIClientError(f"ComfyUI image request failed with status {exc.code}") from exc
        except (URLError, TimeoutError, OSError) as exc:
            raise ComfyUIUnavailableError(f"ComfyUI is unavailable at {self._base_url}") from exc

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

    def _read_json(self, request: Request | str) -> dict[str, Any]:
        try:
            with urllib.request.urlopen(request, timeout=self._timeout_seconds) as response:
                payload = response.read()
        except HTTPError as exc:
            raise ComfyUIClientError(f"ComfyUI request failed with status {exc.code}") from exc
        except (URLError, TimeoutError, OSError) as exc:
            raise ComfyUIUnavailableError(f"ComfyUI is unavailable at {self._base_url}") from exc
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
