from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from app.schemas.file import FilePurpose, FileResponse
from app.services.files.file_service import (
    FileNotFoundError,
    FileServiceError,
    FileTooLargeError,
    UnsupportedFileTypeError,
    file_service,
)

router = APIRouter(prefix="/files", tags=["Files"])


@router.post("", response_model=FileResponse, status_code=status.HTTP_201_CREATED)
def upload_file(file: UploadFile = File(...), purpose: FilePurpose = Form(...)) -> FileResponse:
    try:
        metadata = file_service.upload_file(file, purpose)
        return FileResponse.from_metadata(metadata)
    except (UnsupportedFileTypeError, FileTooLargeError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/{file_id}", response_model=FileResponse)
def get_file(file_id: str) -> FileResponse:
    try:
        return FileResponse.from_metadata(file_service.get_file(file_id))
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_file(file_id: str) -> None:
    try:
        file_service.delete_file(file_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except FileServiceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
