import os
from pathlib import Path
from typing import Any, Literal
from urllib.parse import quote

from pydantic import BaseModel, Field

from app.services.comfyui.client import ComfyUIClient
from app.services.comfyui.workflow import ComfyUIWorkflowTemplate


DEFAULT_WORKFLOW_TEMPLATE = (
    Path(__file__).resolve().parent
    / "comfyui"
    / "templates"
    / "flux1_schnell_fp8_text_to_image.json"
)
DEFAULT_COMFYUI_OUTPUT_DIR = Path("/3241903007/workstation/LYJ/ComfyUI/output")

ImageTaskStatus = Literal["pending", "running", "completed", "failed"]


class ImageResultNotFoundError(FileNotFoundError):
    pass


class InvalidImageResultError(ValueError):
    pass


class ImageGenerationRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=4000)
    width: int = Field(default=1024, ge=64, le=2048)
    height: int = Field(default=1024, ge=64, le=2048)


class ImageGenerationResponse(BaseModel):
    task_id: str
    status: str = "running"


class ImageGenerationStatus(BaseModel):
    task_id: str
    status: ImageTaskStatus
    progress: int = Field(ge=0, le=100)
    image_url: str | None = None


class ImageService:
    def __init__(
        self,
        client: ComfyUIClient,
        workflow_template_path: Path = DEFAULT_WORKFLOW_TEMPLATE,
        output_dir: Path = DEFAULT_COMFYUI_OUTPUT_DIR,
    ) -> None:
        self._client = client
        self._workflow_template = ComfyUIWorkflowTemplate(workflow_template_path)
        self._output_dir = output_dir

    def generate_image(self, request: ImageGenerationRequest) -> ImageGenerationResponse:
        workflow = self._workflow_template.render(
            prompt=request.prompt,
            width=request.width,
            height=request.height,
        )
        prompt_id = self._client.submit_workflow(workflow)
        return ImageGenerationResponse(task_id=prompt_id, status="running")

    def get_generation_status(self, task_id: str) -> ImageGenerationStatus:
        history = self._client.get_history(task_id)
        task_history = history.get(task_id)
        if not isinstance(task_history, dict):
            return ImageGenerationStatus(task_id=task_id, status="running", progress=50, image_url=None)

        status_payload = task_history.get("status", {})
        if not isinstance(status_payload, dict):
            status_payload = {}

        status_str = str(status_payload.get("status_str", "")).lower()
        completed = status_payload.get("completed") is True

        if status_str in {"error", "failed"}:
            return ImageGenerationStatus(task_id=task_id, status="failed", progress=100, image_url=None)

        if completed:
            filename = self._extract_first_output_filename(task_history)
            image_url = f"/api/v1/images/result/{quote(filename)}" if filename else None
            return ImageGenerationStatus(
                task_id=task_id,
                status="completed" if image_url else "failed",
                progress=100,
                image_url=image_url,
            )

        return ImageGenerationStatus(task_id=task_id, status="running", progress=50, image_url=None)

    def get_result_path(self, filename: str) -> Path:
        if not filename or "/" in filename or "\\" in filename or filename in {".", ".."}:
            raise InvalidImageResultError("Invalid image filename")
        path = (self._output_dir / filename).resolve()
        output_root = self._output_dir.resolve()
        if output_root not in path.parents and path != output_root:
            raise InvalidImageResultError("Invalid image filename")
        if not path.is_file():
            raise ImageResultNotFoundError(f"Image result not found: {filename}")
        return path

    def _extract_first_output_filename(self, task_history: dict[str, Any]) -> str | None:
        outputs = task_history.get("outputs", {})
        if not isinstance(outputs, dict):
            return None
        for output in outputs.values():
            if not isinstance(output, dict):
                continue
            images = output.get("images", [])
            if not isinstance(images, list):
                continue
            for image in images:
                if not isinstance(image, dict):
                    continue
                filename = image.get("filename")
                image_type = image.get("type", "output")
                subfolder = image.get("subfolder", "")
                if isinstance(filename, str) and filename and image_type == "output" and subfolder in {"", None}:
                    return filename
        return None


def _build_default_client() -> ComfyUIClient:
    base_url = os.getenv("AI_STUDIO_COMFYUI_BASE_URL", "http://127.0.0.1:8188")
    timeout_seconds = int(os.getenv("AI_STUDIO_COMFYUI_TIMEOUT_SECONDS", "30"))
    return ComfyUIClient(base_url=base_url, timeout_seconds=timeout_seconds)


def _build_default_output_dir() -> Path:
    return Path(os.getenv("AI_STUDIO_COMFYUI_OUTPUT_DIR", str(DEFAULT_COMFYUI_OUTPUT_DIR)))


image_service = ImageService(client=_build_default_client(), output_dir=_build_default_output_dir())
