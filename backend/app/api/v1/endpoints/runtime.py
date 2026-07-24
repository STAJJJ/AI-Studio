from pydantic import BaseModel
from fastapi import APIRouter

from app.core.config import get_settings
from app.services.comfyui.model_registry import ImageModelRegistry


router = APIRouter(prefix="/runtime", tags=["Runtime"])


class RuntimeModelResponse(BaseModel):
    id: str
    name: str
    width: int
    height: int


class RuntimeResponse(BaseModel):
    current_model: str
    current_model_id: str
    engine: str
    backend: str
    gpu: str
    status: str
    models: list[RuntimeModelResponse]


@router.get("", response_model=RuntimeResponse)
def get_runtime() -> RuntimeResponse:
    settings = get_settings()
    registry = ImageModelRegistry(
        default_model_id=settings.default_image_model,
        sd15_checkpoint=settings.sd15_checkpoint,
        sdxl_lightning_checkpoint=settings.sdxl_lightning_checkpoint,
    )
    current_model = registry.get_default_model()
    return RuntimeResponse(
        current_model=current_model.name,
        current_model_id=current_model.id,
        engine="ComfyUI",
        backend="FastAPI",
        gpu=settings.runtime_gpu_name,
        status="Ready",
        models=[
            RuntimeModelResponse(id=model.id, name=model.name, width=model.width, height=model.height)
            for model in registry.list_models()
        ],
    )
