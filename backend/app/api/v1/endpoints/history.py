from typing import Annotated
from urllib.parse import quote

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import FileResponse, Response

from app.schemas.history import WorkflowRunDetailResponse, WorkflowRunListResponse, WorkflowRunStatus, WorkflowType
from app.services.history.repository import WorkflowRunNotFoundError
from app.services.files.file_service import FileNotFoundError, file_service
from app.services.history.service import workflow_history_service
from app.services.comfyui.client import ComfyUIClientError, ComfyUIImageNotFoundError, ComfyUIUnavailableError
from app.services.image_service import InvalidImageResultError, image_service

router = APIRouter(prefix="/history", tags=["History"])


@router.get("", response_model=WorkflowRunListResponse)
def list_history(
    workflow_type: WorkflowType | None = None,
    status_filter: WorkflowRunStatus | None = Query(default=None, alias="status"),
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> WorkflowRunListResponse:
    return workflow_history_service.list_runs(
        workflow_type=workflow_type, status=status_filter, limit=limit, offset=offset
    )


@router.get("/{run_id}", response_model=WorkflowRunDetailResponse)
def get_history_run(run_id: str) -> WorkflowRunDetailResponse:
    try:
        return workflow_history_service.to_detail_response(workflow_history_service.get_run(run_id))
    except WorkflowRunNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/{run_id}/result")
def get_history_result(run_id: str) -> Response:
    try:
        run = workflow_history_service.get_run(run_id)
        if run.result_file_id is None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Workflow result is not ready")
        if run.result_file_id.startswith("image:"):
            filename = run.result_file_id.removeprefix("image:")
            image = image_service.get_result_image(filename)
            return Response(
                content=image.content,
                media_type=image.content_type,
                headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(image.filename)}"},
            )
        metadata = file_service.get_file(run.result_file_id)
        return FileResponse(path=metadata.path, media_type=metadata.content_type, filename=metadata.filename)
    except HTTPException:
        raise
    except WorkflowRunNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InvalidImageResultError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except ComfyUIImageNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ComfyUIUnavailableError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except ComfyUIClientError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
