from enum import Enum
from pathlib import Path

from pydantic import BaseModel


class FilePurpose(str, Enum):
    source_face = "source_face"
    target_image = "target_image"
    target_video = "target_video"
    output = "output"


class FileMetadata(BaseModel):
    id: str
    filename: str
    content_type: str
    purpose: FilePurpose
    size_bytes: int
    path: Path


class FileResponse(BaseModel):
    id: str
    filename: str
    content_type: str
    purpose: FilePurpose
    size_bytes: int

    @classmethod
    def from_metadata(cls, metadata: FileMetadata) -> "FileResponse":
        return cls(
            id=metadata.id,
            filename=metadata.filename,
            content_type=metadata.content_type,
            purpose=metadata.purpose,
            size_bytes=metadata.size_bytes,
        )
