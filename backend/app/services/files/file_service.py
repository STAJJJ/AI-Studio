import json
import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.core.config import Settings, get_settings
from app.schemas.file import FileMetadata, FilePurpose


class FileServiceError(ValueError):
    pass


class FileNotFoundError(FileServiceError):
    pass


class UnsupportedFileTypeError(FileServiceError):
    pass


class FileTooLargeError(FileServiceError):
    pass


class FileService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._upload_dir = settings.upload_dir
        self._output_dir = settings.output_dir
        self._metadata_dir = self._upload_dir / ".metadata"
        self._ensure_directories()

    def upload_file(self, upload_file: UploadFile, purpose: FilePurpose) -> FileMetadata:
        content_type = upload_file.content_type or "application/octet-stream"
        if content_type not in self._settings.allowed_mime_types:
            raise UnsupportedFileTypeError(f"Unsupported file type: {content_type}")

        file_id = f"file_{uuid4().hex}"
        safe_name = Path(upload_file.filename or "upload.bin").name
        destination = self._upload_dir / file_id / safe_name
        destination.parent.mkdir(parents=True, exist_ok=True)

        size_bytes = self._write_upload(upload_file, destination)
        metadata = FileMetadata(
            id=file_id,
            filename=safe_name,
            content_type=content_type,
            purpose=purpose,
            size_bytes=size_bytes,
            path=destination,
        )
        self._save_metadata(metadata)
        return metadata

    def register_output_file(self, source_path: Path, filename: str, content_type: str = "image/png") -> FileMetadata:
        if not source_path.exists():
            raise FileNotFoundError(f"Output source does not exist: {source_path}")

        file_id = f"file_{uuid4().hex}"
        safe_name = Path(filename).name
        destination = self._output_dir / file_id / safe_name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source_path, destination)

        metadata = FileMetadata(
            id=file_id,
            filename=safe_name,
            content_type=content_type,
            purpose=FilePurpose.output,
            size_bytes=destination.stat().st_size,
            path=destination,
        )
        self._save_metadata(metadata)
        return metadata

    def get_file(self, file_id: str) -> FileMetadata:
        path = self._metadata_path(file_id)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_id}")
        return FileMetadata.model_validate_json(path.read_text())

    def delete_file(self, file_id: str) -> None:
        metadata = self.get_file(file_id)
        if metadata.path.exists():
            shutil.rmtree(metadata.path.parent, ignore_errors=True)
        self._metadata_path(file_id).unlink(missing_ok=True)

    def _write_upload(self, upload_file: UploadFile, destination: Path) -> int:
        size_bytes = 0
        with destination.open("wb") as buffer:
            while chunk := upload_file.file.read(1024 * 1024):
                size_bytes += len(chunk)
                if size_bytes > self._settings.max_file_size_bytes:
                    buffer.close()
                    shutil.rmtree(destination.parent, ignore_errors=True)
                    raise FileTooLargeError("File exceeds max upload size")
                buffer.write(chunk)
        return size_bytes

    def _save_metadata(self, metadata: FileMetadata) -> None:
        self._metadata_path(metadata.id).write_text(metadata.model_dump_json())

    def _metadata_path(self, file_id: str) -> Path:
        return self._metadata_dir / f"{file_id}.json"

    def _ensure_directories(self) -> None:
        self._upload_dir.mkdir(parents=True, exist_ok=True)
        self._output_dir.mkdir(parents=True, exist_ok=True)
        self._metadata_dir.mkdir(parents=True, exist_ok=True)


file_service = FileService(get_settings())
