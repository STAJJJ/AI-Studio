import json
from pathlib import Path

import pytest
from sqlalchemy import text

from app.core.database import Base, create_sqlite_engine, create_session_factory
from app.models.workflow_run import WorkflowRunORM
from app.schemas.history import WorkflowRunCreate, WorkflowRunStatus, WorkflowType
from app.services.history.repository import DuplicateWorkflowRunError, WorkflowRunNotFoundError
from app.services.history.sqlite_repository import SQLiteWorkflowHistoryRepository


def make_run(
    *,
    title: str = "Run",
    workflow_type: WorkflowType = WorkflowType.image_generation,
    status: WorkflowRunStatus = WorkflowRunStatus.running,
    external_task_id: str = "task_1",
) -> WorkflowRunCreate:
    return WorkflowRunCreate(
        workflow_type=workflow_type,
        runtime="comfyui" if workflow_type == WorkflowType.image_generation else "facefusion",
        provider="sd15" if workflow_type == WorkflowType.image_generation else "facefusion",
        status=status,
        progress=100 if status in {WorkflowRunStatus.succeeded, WorkflowRunStatus.failed} else 0,
        title=title,
        input_summary="summary",
        input_payload={"prompt": "A cat", "model": "sd15"} if workflow_type == WorkflowType.image_generation else {
            "source_file_id": "file_a",
            "target_file_id": "file_b",
        },
        output_payload={"filename": "result.png"} if status == WorkflowRunStatus.succeeded else {},
        result_file_id="file_result" if status == WorkflowRunStatus.succeeded else None,
        error_code="TASK_FAILED" if status == WorkflowRunStatus.failed else None,
        error_message="failed" if status == WorkflowRunStatus.failed else None,
        external_task_id=external_task_id,
    )


def make_repository(database_path: Path) -> SQLiteWorkflowHistoryRepository:
    engine = create_sqlite_engine(f"sqlite:///{database_path}")
    Base.metadata.create_all(bind=engine)
    return SQLiteWorkflowHistoryRepository(create_session_factory(engine))


def test_sqlite_create_get_and_payload_round_trip(tmp_path: Path) -> None:
    repository = make_repository(tmp_path / "history.db")

    created = repository.create(make_run())
    fetched = repository.get(created.id)

    assert fetched.id == created.id
    assert fetched.workflow_type == WorkflowType.image_generation
    assert fetched.input_payload == {"prompt": "A cat", "model": "sd15"}
    assert fetched.output_payload == {}


def test_sqlite_update_sets_completed_at_and_result_file_id(tmp_path: Path) -> None:
    repository = make_repository(tmp_path / "history.db")
    run = repository.create(make_run())

    updated = repository.update(
        run.id,
        status=WorkflowRunStatus.succeeded,
        progress=100,
        result_file_id="file_result",
        output_payload={"filename": "result.png"},
    )

    assert updated.status == WorkflowRunStatus.succeeded
    assert updated.completed_at is not None
    assert updated.result_file_id == "file_result"
    assert updated.output_payload == {"filename": "result.png"}


def test_sqlite_list_filters_paginates_and_counts_total(tmp_path: Path) -> None:
    repository = make_repository(tmp_path / "history.db")
    first = repository.create(make_run(title="First", external_task_id="prompt_1"))
    second = repository.create(make_run(title="Second", external_task_id="prompt_2"))
    face = repository.create(
        make_run(
            title="Face",
            workflow_type=WorkflowType.face_swap,
            status=WorkflowRunStatus.failed,
            external_task_id="task_face",
        )
    )

    items, total = repository.list(limit=2, offset=0)
    face_items, face_total = repository.list(workflow_type=WorkflowType.face_swap, limit=10, offset=0)
    failed_items, failed_total = repository.list(status=WorkflowRunStatus.failed, limit=10, offset=0)
    page_items, page_total = repository.list(limit=1, offset=1)

    assert total == 3
    assert len(items) == 2
    assert items[0].id in {face.id, second.id, first.id}
    assert face_total == 1
    assert face_items[0].id == face.id
    assert failed_total == 1
    assert failed_items[0].id == face.id
    assert page_total == 3
    assert len(page_items) == 1


def test_sqlite_external_task_mapping_and_duplicate_protection(tmp_path: Path) -> None:
    repository = make_repository(tmp_path / "history.db")
    created = repository.create(make_run(external_task_id="prompt_1"))

    assert repository.get_by_external_task_id(WorkflowType.image_generation, "prompt_1").id == created.id
    with pytest.raises(DuplicateWorkflowRunError):
        repository.create(make_run(external_task_id="prompt_1"))


def test_sqlite_missing_run_raises_clear_error(tmp_path: Path) -> None:
    repository = make_repository(tmp_path / "history.db")

    with pytest.raises(WorkflowRunNotFoundError):
        repository.get("run_missing")
    with pytest.raises(WorkflowRunNotFoundError):
        repository.update("run_missing", status=WorkflowRunStatus.failed)


def test_sqlite_persists_across_repository_instances(tmp_path: Path) -> None:
    database_path = tmp_path / "history.db"
    first_repository = make_repository(database_path)
    created = first_repository.create(make_run(external_task_id="prompt_1"))

    second_repository = make_repository(database_path)

    assert second_repository.get(created.id).external_task_id == "prompt_1"
    assert second_repository.get_by_external_task_id(WorkflowType.image_generation, "prompt_1").id == created.id


def test_sqlite_rejects_absolute_paths_before_database_write(tmp_path: Path) -> None:
    repository = make_repository(tmp_path / "history.db")

    with pytest.raises(ValueError):
        repository.create(
            WorkflowRunCreate(
                workflow_type=WorkflowType.image_generation,
                runtime="comfyui",
                provider="sd15",
                status=WorkflowRunStatus.running,
                progress=0,
                title="bad",
                input_summary="bad",
                input_payload={"source_path": "/Users/lyj/private.png"},
                output_payload={},
                external_task_id="bad",
            )
        )


def test_sqlite_invalid_json_payload_raises_clear_error(tmp_path: Path) -> None:
    database_path = tmp_path / "history.db"
    repository = make_repository(database_path)
    run = repository.create(make_run())

    with repository._session_factory() as session:
        session.execute(
            text("UPDATE workflow_runs SET input_payload = :payload WHERE id = :id"),
            {"payload": "{not-json", "id": run.id},
        )
        session.commit()

    with pytest.raises(ValueError, match="Invalid workflow history JSON"):
        repository.get(run.id)


def test_sqlite_nullable_fields_and_continuous_creates(tmp_path: Path) -> None:
    repository = make_repository(tmp_path / "history.db")
    pending = repository.create(make_run(external_task_id="prompt_1"))
    succeeded = repository.create(
        make_run(status=WorkflowRunStatus.succeeded, external_task_id="prompt_2", title="Succeeded")
    )

    assert pending.result_file_id is None
    assert pending.completed_at is None
    assert succeeded.result_file_id == "file_result"
    assert succeeded.completed_at is not None
    assert repository.get_by_external_task_id(WorkflowType.image_generation, "prompt_2").id == succeeded.id


def test_sqlite_model_stores_json_as_text(tmp_path: Path) -> None:
    repository = make_repository(tmp_path / "history.db")
    run = repository.create(make_run())

    with repository._session_factory() as session:
        row = session.get(WorkflowRunORM, run.id)

    assert row is not None
    assert isinstance(row.input_payload, str)
    assert json.loads(row.input_payload) == {"model": "sd15", "prompt": "A cat"}
