from sqlalchemy import Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class WorkflowRunORM(Base):
    __tablename__ = "workflow_runs"
    __table_args__ = (
        UniqueConstraint("workflow_type", "external_task_id", name="uq_workflow_runs_type_external_task"),
        Index("ix_workflow_runs_workflow_type", "workflow_type"),
        Index("ix_workflow_runs_status", "status"),
        Index("ix_workflow_runs_created_at", "created_at"),
        Index("ix_workflow_runs_external_task_id", "external_task_id"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True)
    workflow_type: Mapped[str] = mapped_column(String, nullable=False)
    runtime: Mapped[str] = mapped_column(String, nullable=False)
    provider: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False)
    progress: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    input_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    input_payload: Mapped[str] = mapped_column(Text, nullable=False)
    output_payload: Mapped[str] = mapped_column(Text, nullable=False)
    result_file_id: Mapped[str | None] = mapped_column(String, nullable=True)
    error_code: Mapped[str | None] = mapped_column(String, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    external_task_id: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[int] = mapped_column(Integer, nullable=False)
    updated_at: Mapped[int] = mapped_column(Integer, nullable=False)
    completed_at: Mapped[int | None] = mapped_column(Integer, nullable=True)
