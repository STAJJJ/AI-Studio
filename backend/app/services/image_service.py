import uuid
from typing import Any, Literal
from urllib.parse import quote

from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.services.comfyui.client import ComfyUIClient, ComfyUIImage
from app.services.comfyui.model_registry import ImageModelRegistry
from app.schemas.history import WorkflowRunStatus, WorkflowType
from app.services.comfyui.workflow import ComfyUIWorkflowTemplate
from app.services.history.repository import WorkflowRunNotFoundError
from app.services.history.service import WorkflowHistoryService, workflow_history_service


ImageTaskStatus = Literal["pending", "running", "completed", "failed"]


class InvalidImageResultError(ValueError):
    pass


class ImageCheckpointNotFoundError(ValueError):
    pass


class ImageGenerationRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=4000)
    model: str | None = None
    width: int | None = Field(default=None, ge=64, le=2048)
    height: int | None = Field(default=None, ge=64, le=2048)


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
        model_registry: ImageModelRegistry | None = None,
        history_service: WorkflowHistoryService | None = None,
    ) -> None:
        self._client = client
        self._model_registry = model_registry or ImageModelRegistry()
        self._history = history_service or workflow_history_service

    def generate_image(self, request: ImageGenerationRequest) -> ImageGenerationResponse:
        model = self._model_registry.get_model(request.model)
        self._ensure_checkpoint_available(model.checkpoint)
        workflow_template = ComfyUIWorkflowTemplate(self._model_registry.get_workflow_path(model.id))
        workflow = workflow_template.render(
            prompt=request.prompt,
            width=request.width or model.width,
            height=request.height or model.height,
            checkpoint=model.checkpoint,
        )
        self._prepare_unique_workflow_run(workflow)
        prompt_id = self._client.submit_workflow(workflow)
        self._history.create_image_generation_run(
            external_task_id=prompt_id,
            model=model.id,
            prompt=request.prompt,
            width=request.width or model.width,
            height=request.height or model.height,
        )
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
            self._update_history_if_present(
                task_id,
                status=WorkflowRunStatus.failed,
                progress=100,
                error_code="COMFYUI_TASK_FAILED",
                error_message="ComfyUI reported task failure",
            )
            return ImageGenerationStatus(task_id=task_id, status="failed", progress=100, image_url=None)

        if completed:
            filename = self._extract_first_output_filename(task_history)
            image_url = f"/api/v1/images/result/{quote(filename)}" if filename else None
            if image_url:
                self._update_history_if_present(
                    task_id,
                    status=WorkflowRunStatus.succeeded,
                    progress=100,
                    result_file_id=f"image:{filename}",
                    output_payload={"filename": filename, "image_url": image_url},
                )
            else:
                self._update_history_if_present(
                    task_id,
                    status=WorkflowRunStatus.failed,
                    progress=100,
                    error_code="COMFYUI_OUTPUT_NOT_FOUND",
                    error_message="ComfyUI completed without an output image",
                )
            return ImageGenerationStatus(
                task_id=task_id,
                status="completed" if image_url else "failed",
                progress=100,
                image_url=image_url,
            )

        self._update_history_if_present(task_id, status=WorkflowRunStatus.running, progress=50)
        return ImageGenerationStatus(task_id=task_id, status="running", progress=50, image_url=None)

    def get_result_image(self, filename: str) -> ComfyUIImage:
        if not filename or "/" in filename or "\\" in filename or filename in {".", ".."}:
            raise InvalidImageResultError("Invalid image filename")
        return self._client.get_image(filename=filename)

    def _ensure_checkpoint_available(self, checkpoint: str) -> None:
        if checkpoint not in self._client.list_checkpoints():
            raise ImageCheckpointNotFoundError(f"ComfyUI checkpoint is not installed: {checkpoint}")

    def _update_history_if_present(self, task_id: str, **changes: object) -> None:
        try:
            self._history.update_by_external_task_id(WorkflowType.image_generation, task_id, **changes)
        except WorkflowRunNotFoundError:
            return

    def _prepare_unique_workflow_run(self, workflow: dict[str, Any]) -> None:
        run_id = uuid.uuid4()
        seed = run_id.int % (2**63 - 1)
        suffix = run_id.hex[:12]

        for node in workflow.values():
            if not isinstance(node, dict):
                continue
            inputs = node.get("inputs")
            if not isinstance(inputs, dict):
                continue

            if node.get("class_type") == "KSampler" and "seed" in inputs:
                inputs["seed"] = seed

            if node.get("class_type") == "SaveImage" and isinstance(inputs.get("filename_prefix"), str):
                inputs["filename_prefix"] = f'{inputs["filename_prefix"]}_{suffix}'

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
    settings = get_settings()
    return ComfyUIClient(base_url=settings.comfyui_base_url, timeout_seconds=settings.comfyui_timeout_seconds)


def _build_default_model_registry() -> ImageModelRegistry:
    settings = get_settings()
    return ImageModelRegistry(
        default_model_id=settings.default_image_model,
        sd15_checkpoint=settings.sd15_checkpoint,
        sdxl_lightning_checkpoint=settings.sdxl_lightning_checkpoint,
    )


image_service = ImageService(
    client=_build_default_client(),
    model_registry=_build_default_model_registry(),
)
