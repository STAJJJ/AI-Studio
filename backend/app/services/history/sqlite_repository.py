import json
from time import time
from typing import Any

from sqlalchemy import Select, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.models.workflow_run import WorkflowRunORM
from app.schemas.history import WorkflowRunCreate, WorkflowRunRecord, WorkflowRunStatus, WorkflowType
from app.services.history.repository import DuplicateWorkflowRunError, WorkflowHistoryRepository, WorkflowRunNotFoundError


class SQLiteWorkflowHistoryRepository(WorkflowHistoryRepository):
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def create(self, data: WorkflowRunCreate) -> WorkflowRunRecord:
        record = WorkflowRunRecord(
            **data.model_dump(),
            completed_at=int(time()) if data.status in {WorkflowRunStatus.succeeded, WorkflowRunStatus.failed} else None,
        )
        row = self._to_orm(record)

        with self._session_factory() as session:
            try:
                session.add(row)
                session.commit()
                session.refresh(row)
                return self._to_record(row)
            except IntegrityError as exc:
                session.rollback()
                raise DuplicateWorkflowRunError(
                    f"Workflow history already exists for {data.workflow_type}:{data.external_task_id}"
                ) from exc
            except Exception:
                session.rollback()
                raise

    def update(self, run_id: str, **changes: object) -> WorkflowRunRecord:
        with self._session_factory() as session:
            row = session.get(WorkflowRunORM, run_id)
            if row is None:
                raise WorkflowRunNotFoundError(f"Workflow history run not found: {run_id}")

            normalized = {key: value for key, value in changes.items() if value is not None and key != "id"}
            status = normalized.get("status")
            if isinstance(status, WorkflowRunStatus):
                normalized["status"] = status.value
            if status in {WorkflowRunStatus.succeeded, WorkflowRunStatus.failed} and row.completed_at is None:
                normalized["completed_at"] = int(time())

            if "workflow_type" in normalized and isinstance(normalized["workflow_type"], WorkflowType):
                normalized["workflow_type"] = normalized["workflow_type"].value
            for payload_key in ("input_payload", "output_payload"):
                if payload_key in normalized:
                    normalized[payload_key] = self._dump_json(normalized[payload_key])

            normalized["updated_at"] = int(time())

            try:
                for key, value in normalized.items():
                    setattr(row, key, value)
                session.commit()
                session.refresh(row)
                return self._to_record(row)
            except IntegrityError as exc:
                session.rollback()
                raise DuplicateWorkflowRunError(f"Workflow history update violates uniqueness: {run_id}") from exc
            except Exception:
                session.rollback()
                raise

    def get(self, run_id: str) -> WorkflowRunRecord:
        with self._session_factory() as session:
            row = session.get(WorkflowRunORM, run_id)
            if row is None:
                raise WorkflowRunNotFoundError(f"Workflow history run not found: {run_id}")
            return self._to_record(row)

    def list(
        self,
        *,
        workflow_type: WorkflowType | None = None,
        status: WorkflowRunStatus | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[WorkflowRunRecord], int]:
        statement: Select[tuple[WorkflowRunORM]] = select(WorkflowRunORM)
        count_statement = select(func.count()).select_from(WorkflowRunORM)

        if workflow_type is not None:
            statement = statement.where(WorkflowRunORM.workflow_type == workflow_type.value)
            count_statement = count_statement.where(WorkflowRunORM.workflow_type == workflow_type.value)
        if status is not None:
            statement = statement.where(WorkflowRunORM.status == status.value)
            count_statement = count_statement.where(WorkflowRunORM.status == status.value)

        statement = statement.order_by(WorkflowRunORM.created_at.desc(), WorkflowRunORM.id.desc()).limit(limit).offset(offset)

        with self._session_factory() as session:
            total = session.scalar(count_statement) or 0
            rows = session.scalars(statement).all()
            return [self._to_record(row) for row in rows], total

    def get_by_external_task_id(self, workflow_type: WorkflowType, external_task_id: str) -> WorkflowRunRecord:
        statement = select(WorkflowRunORM).where(
            WorkflowRunORM.workflow_type == workflow_type.value,
            WorkflowRunORM.external_task_id == external_task_id,
        )
        with self._session_factory() as session:
            row = session.scalars(statement).first()
            if row is None:
                raise WorkflowRunNotFoundError(f"Workflow history run not found: {workflow_type}:{external_task_id}")
            return self._to_record(row)

    def _to_orm(self, record: WorkflowRunRecord) -> WorkflowRunORM:
        return WorkflowRunORM(
            id=record.id,
            workflow_type=record.workflow_type.value,
            runtime=record.runtime,
            provider=record.provider,
            status=record.status.value,
            progress=record.progress,
            title=record.title,
            input_summary=record.input_summary,
            input_payload=self._dump_json(record.input_payload),
            output_payload=self._dump_json(record.output_payload),
            result_file_id=record.result_file_id,
            error_code=record.error_code,
            error_message=record.error_message,
            external_task_id=record.external_task_id,
            created_at=record.created_at,
            updated_at=record.updated_at,
            completed_at=record.completed_at,
        )

    def _to_record(self, row: WorkflowRunORM) -> WorkflowRunRecord:
        return WorkflowRunRecord(
            id=row.id,
            workflow_type=WorkflowType(row.workflow_type),
            runtime=row.runtime,
            provider=row.provider or "",
            status=WorkflowRunStatus(row.status),
            progress=row.progress,
            title=row.title,
            input_summary=row.input_summary or "",
            input_payload=self._load_json(row.input_payload),
            output_payload=self._load_json(row.output_payload),
            result_file_id=row.result_file_id,
            error_code=row.error_code,
            error_message=row.error_message,
            external_task_id=row.external_task_id or "",
            created_at=row.created_at,
            updated_at=row.updated_at,
            completed_at=row.completed_at,
        )

    def _dump_json(self, value: object) -> str:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    def _load_json(self, value: str) -> dict[str, Any]:
        try:
            decoded = json.loads(value)
        except json.JSONDecodeError as exc:
            raise ValueError("Invalid workflow history JSON payload") from exc
        if not isinstance(decoded, dict):
            raise ValueError("Invalid workflow history JSON payload")
        return decoded
