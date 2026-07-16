from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse

from app.services.comfyui.client import ComfyUIClientError
from app.services.comfyui.model_registry import UnknownImageModelError
from app.services.comfyui.workflow import WorkflowTemplateError
from app.services.image_service import (
    ImageGenerationRequest,
    ImageGenerationResponse,
    ImageGenerationStatus,
    ImageResultNotFoundError,
    InvalidImageResultError,
    image_service,
)

router = APIRouter(prefix="/images", tags=["Images"])


@router.post("/generate", response_model=ImageGenerationResponse, status_code=status.HTTP_202_ACCEPTED)
def generate_image(request: ImageGenerationRequest) -> ImageGenerationResponse:
    try:
        return image_service.generate_image(request)
    except UnknownImageModelError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except WorkflowTemplateError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
    except ComfyUIClientError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc


@router.get("/tasks/{task_id}", response_model=ImageGenerationStatus)
def get_image_task_status(task_id: str) -> ImageGenerationStatus:
    try:
        return image_service.get_generation_status(task_id)
    except ComfyUIClientError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc


@router.get("/result/{filename}")
def get_image_result(filename: str) -> FileResponse:
    try:
        result_path = image_service.get_result_path(filename)
        return FileResponse(path=result_path, media_type="image/png", filename=filename)
    except InvalidImageResultError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except ImageResultNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
