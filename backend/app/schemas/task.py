from enum import Enum
from time import time
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    pending = "pending"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"


class TaskResult(BaseModel):
    file_id: str
    download_url: str


class TaskError(BaseModel):
    code: str
    message: str


class TaskRecord(BaseModel):
    id: str = Field(default_factory=lambda: f"task_{uuid4().hex}")
    type: str
    status: TaskStatus = TaskStatus.pending
    progress: int = 0
    message: str = "Pending"
    created_at: int = Field(default_factory=lambda: int(time()))
    updated_at: int = Field(default_factory=lambda: int(time()))
    result: TaskResult | None = None
    error: TaskError | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class TaskResponse(BaseModel):
    id: str
    type: str
    status: TaskStatus
    progress: int
    message: str
    created_at: int
    updated_at: int
    result: TaskResult | None = None
    error: TaskError | None = None

    @classmethod
    def from_record(cls, record: TaskRecord) -> "TaskResponse":
        return cls(
            id=record.id,
            type=record.type,
            status=record.status,
            progress=record.progress,
            message=record.message,
            created_at=record.created_at,
            updated_at=record.updated_at,
            result=record.result,
            error=record.error,
        )


class FaceSwapTaskCreateRequest(BaseModel):
    source_file_id: str
    target_file_id: str
    options: dict[str, Any] = Field(default_factory=dict)
