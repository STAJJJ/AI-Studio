from fastapi import APIRouter, HTTPException, status

from app.services.comfyui.client import ComfyUIClientError
from app.services.comfyui.workflow import WorkflowTemplateError
from app.services.image_service import ImageGenerationRequest, ImageGenerationResponse, image_service

router = APIRouter(prefix="/images", tags=["Images"])


@router.post("/generate", response_model=ImageGenerationResponse, status_code=status.HTTP_202_ACCEPTED)
def generate_image(request: ImageGenerationRequest) -> ImageGenerationResponse:
    try:
        return image_service.generate_image(request)
    except WorkflowTemplateError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
    except ComfyUIClientError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
