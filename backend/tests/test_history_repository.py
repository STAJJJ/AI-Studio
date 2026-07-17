from app.schemas.history import WorkflowRunCreate, WorkflowRunStatus, WorkflowType
from app.services.history.memory_repository import DuplicateWorkflowRunError, InMemoryWorkflowHistoryRepository


def make_run(title: str = "Run", external_task_id: str = "task_1") -> WorkflowRunCreate:
    return WorkflowRunCreate(
        workflow_type=WorkflowType.image_generation,
        runtime="comfyui",
        provider="sd15",
        status=WorkflowRunStatus.running,
        progress=0,
        title=title,
        input_summary="A prompt",
        input_payload={"prompt": "A prompt", "width": 512, "height": 512, "model": "sd15"},
        output_payload={},
        external_task_id=external_task_id,
    )


def test_repository_create_get_and_dynamic_ordering() -> None:
    repository = InMemoryWorkflowHistoryRepository()

    first = repository.create(make_run(title="First", external_task_id="prompt_1"))
    second = repository.create(make_run(title="Second", external_task_id="prompt_2"))

    assert repository.get(first.id).title == "First"
    items, total = repository.list(limit=20, offset=0)
    assert total == 2
    assert [item.id for item in items] == [second.id, first.id]


def test_repository_update_sets_completed_at_for_terminal_status() -> None:
    repository = InMemoryWorkflowHistoryRepository()
    run = repository.create(make_run())

    updated = repository.update(run.id, status=WorkflowRunStatus.succeeded, progress=100, result_file_id="file_1")

    assert updated.status == WorkflowRunStatus.succeeded
    assert updated.completed_at is not None
    assert updated.result_file_id == "file_1"


def test_repository_filters_paginates_and_maps_external_task_id() -> None:
    repository = InMemoryWorkflowHistoryRepository()
    image = repository.create(make_run(title="Image", external_task_id="prompt_1"))
    face = repository.create(
        WorkflowRunCreate(
            workflow_type=WorkflowType.face_swap,
            runtime="facefusion",
            provider="facefusion",
            status=WorkflowRunStatus.failed,
            progress=100,
            title="Face Swap",
            input_summary="source -> target",
            input_payload={"source_file_id": "file_a", "target_file_id": "file_b"},
            output_payload={},
            external_task_id="task_1",
        )
    )

    image_items, image_total = repository.list(workflow_type=WorkflowType.image_generation, limit=10, offset=0)
    failed_items, failed_total = repository.list(status=WorkflowRunStatus.failed, limit=10, offset=0)
    page_items, page_total = repository.list(limit=1, offset=1)

    assert image_total == 1
    assert image_items[0].id == image.id
    assert failed_total == 1
    assert failed_items[0].id == face.id
    assert page_total == 2
    assert len(page_items) == 1
    assert repository.get_by_external_task_id(WorkflowType.face_swap, "task_1").id == face.id


def test_repository_rejects_duplicate_external_task_for_same_workflow_type() -> None:
    repository = InMemoryWorkflowHistoryRepository()
    repository.create(make_run(external_task_id="prompt_1"))

    try:
        repository.create(make_run(external_task_id="prompt_1"))
    except DuplicateWorkflowRunError:
        pass
    else:
        raise AssertionError("Expected duplicate external task id to be rejected")
