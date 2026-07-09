from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse

from app.schemas.task import FaceSwapTaskCreateRequest, TaskResponse
from app.services.face_swap_service import face_swap_service
from app.services.files.file_service import FileNotFoundError, file_service
from app.services.jobs.task_manager import TaskNotFoundError, TaskResultNotReadyError, task_manager

router = APIRouter(tags=["Tasks"])


@router.post("/face-swap/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_face_swap_task(request: FaceSwapTaskCreateRequest) -> TaskResponse:
    try:
        return face_swap_service.create_task(request)
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/tasks/{task_id}", response_model=TaskResponse)
def get_task(task_id: str) -> TaskResponse:
    try:
        return TaskResponse.from_record(task_manager.get_task(task_id))
    except TaskNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/tasks/{task_id}/result")
def get_task_result(task_id: str) -> FileResponse:
    try:
        task = task_manager.require_result(task_id)
        assert task.result is not None
        metadata = file_service.get_file(task.result.file_id)
        return FileResponse(path=metadata.path, media_type=metadata.content_type, filename=metadata.filename)
    except TaskNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except TaskResultNotReadyError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
