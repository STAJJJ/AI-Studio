import os
from pathlib import Path

from pydantic import BaseModel, Field

from app.services.comfyui.client import ComfyUIClient
from app.services.comfyui.workflow import ComfyUIWorkflowTemplate


DEFAULT_WORKFLOW_TEMPLATE = (
    Path(__file__).resolve().parent
    / "comfyui"
    / "templates"
    / "flux1_schnell_fp8_text_to_image.json"
)


class ImageGenerationRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=4000)
    width: int = Field(default=1024, ge=64, le=2048)
    height: int = Field(default=1024, ge=64, le=2048)


class ImageGenerationResponse(BaseModel):
    task_id: str
    status: str = "running"


class ImageService:
    def __init__(self, client: ComfyUIClient, workflow_template_path: Path = DEFAULT_WORKFLOW_TEMPLATE) -> None:
        self._client = client
        self._workflow_template = ComfyUIWorkflowTemplate(workflow_template_path)

    def generate_image(self, request: ImageGenerationRequest) -> ImageGenerationResponse:
        workflow = self._workflow_template.render(
            prompt=request.prompt,
            width=request.width,
            height=request.height,
        )
        prompt_id = self._client.submit_workflow(workflow)
        return ImageGenerationResponse(task_id=prompt_id, status="running")


def _build_default_client() -> ComfyUIClient:
    base_url = os.getenv("AI_STUDIO_COMFYUI_BASE_URL", "http://127.0.0.1:8188")
    timeout_seconds = int(os.getenv("AI_STUDIO_COMFYUI_TIMEOUT_SECONDS", "30"))
    return ComfyUIClient(base_url=base_url, timeout_seconds=timeout_seconds)


image_service = ImageService(client=_build_default_client())
