from fastapi import APIRouter

from app.schemas.health import HealthResponse
from app.services.health_service import health_service

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("", response_model=HealthResponse)
def health_check() -> HealthResponse:
    return health_service.get_status()
