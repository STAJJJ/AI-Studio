from enum import Enum
from time import time
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


class WorkflowType(str, Enum):
    image_generation = "image_generation"
    face_swap = "face_swap"


class WorkflowRunStatus(str, Enum):
    pending = "pending"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"


class WorkflowRunCreate(BaseModel):
    workflow_type: WorkflowType
    runtime: str
    provider: str
    status: WorkflowRunStatus = WorkflowRunStatus.pending
    progress: int = Field(default=0, ge=0, le=100)
    title: str
    input_summary: str
    input_payload: dict[str, Any] = Field(default_factory=dict)
    output_payload: dict[str, Any] = Field(default_factory=dict)
    result_file_id: str | None = None
    error_code: str | None = None
    error_message: str | None = None
    external_task_id: str

    @field_validator("input_payload", "output_payload")
    @classmethod
    def reject_absolute_paths(cls, value: dict[str, Any]) -> dict[str, Any]:
        serialized = str(value)
        if "/Users/" in serialized or "/3241903007/" in serialized:
            raise ValueError("Workflow history payload must not contain absolute server paths")
        return value


class WorkflowRunUpdate(BaseModel):
    status: WorkflowRunStatus | None = None
    progress: int | None = Field(default=None, ge=0, le=100)
    title: str | None = None
    input_summary: str | None = None
    input_payload: dict[str, Any] | None = None
    output_payload: dict[str, Any] | None = None
    result_file_id: str | None = None
    error_code: str | None = None
    error_message: str | None = None

    @field_validator("input_payload", "output_payload")
    @classmethod
    def reject_absolute_paths(cls, value: dict[str, Any] | None) -> dict[str, Any] | None:
        if value is None:
            return value
        serialized = str(value)
        if "/Users/" in serialized or "/3241903007/" in serialized:
            raise ValueError("Workflow history payload must not contain absolute server paths")
        return value


class WorkflowRunRecord(BaseModel):
    id: str = Field(default_factory=lambda: f"run_{uuid4().hex}")
    workflow_type: WorkflowType
    runtime: str
    provider: str
    status: WorkflowRunStatus = WorkflowRunStatus.pending
    progress: int = Field(default=0, ge=0, le=100)
    title: str
    input_summary: str
    input_payload: dict[str, Any] = Field(default_factory=dict)
    output_payload: dict[str, Any] = Field(default_factory=dict)
    result_file_id: str | None = None
    error_code: str | None = None
    error_message: str | None = None
    external_task_id: str
    created_at: int = Field(default_factory=lambda: int(time()))
    updated_at: int = Field(default_factory=lambda: int(time()))
    completed_at: int | None = None


class WorkflowRunSummaryResponse(BaseModel):
    id: str
    workflow_type: WorkflowType
    runtime: str
    provider: str
    status: WorkflowRunStatus
    progress: int
    title: str
    input_summary: str
    result_url: str | None = None
    external_task_id: str
    created_at: int
    updated_at: int
    completed_at: int | None = None


class WorkflowRunDetailResponse(WorkflowRunSummaryResponse):
    input_payload: dict[str, Any]
    output_payload: dict[str, Any]
    result_file_id: str | None = None
    error_code: str | None = None
    error_message: str | None = None


class WorkflowRunListResponse(BaseModel):
    items: list[WorkflowRunSummaryResponse]
    total: int
    limit: int
    offset: int
