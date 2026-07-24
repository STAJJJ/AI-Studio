import json
from pathlib import Path

import pytest

from app.services.comfyui.model_registry import ImageModelRegistry
from app.services.comfyui.client import ComfyUIImage
from app.schemas.history import WorkflowRunStatus, WorkflowType
from app.services.history.memory_repository import InMemoryWorkflowHistoryRepository
from app.services.history.service import WorkflowHistoryService
from app.services.image_service import (
    ImageCheckpointNotFoundError,
    ImageGenerationRequest,
    ImageGenerationStatus,
    ImageService,
)


class FakeComfyUIClient:
    def __init__(self) -> None:
        self.submitted_workflow = None
        self.history = {}
        self.available_checkpoints = {
            "v1-5-pruned-emaonly-fp16.safetensors",
            "sdxl_lightning_4step.safetensors",
        }

    def submit_workflow(self, workflow):
        self.submitted_workflow = workflow
        return "prompt-abc"

    def get_history(self, task_id):
        return self.history

    def get_image(self, filename, subfolder="", image_type="output"):
        return ComfyUIImage(content=b"remote-png", content_type="image/png", filename=filename)

    def list_checkpoints(self):
        return self.available_checkpoints


def test_image_service_loads_template_and_submits_rendered_workflow(tmp_path: Path) -> None:
    template_dir = tmp_path / "templates"
    template_dir.mkdir()
    template_path = template_dir / "sd15_text_to_image.json"
    template_path.write_text(
        json.dumps(
            {
                "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "{{checkpoint}}"}},
                "2": {"class_type": "CLIPTextEncode", "inputs": {"text": "{{prompt}}"}},
                "3": {"class_type": "EmptyLatentImage", "inputs": {"width": "{{width}}", "height": "{{height}}", "batch_size": 1}},
            }
        )
    )
    client = FakeComfyUIClient()
    registry = ImageModelRegistry(default_model_id="sd15", template_dir=template_dir)
    service = ImageService(client=client, model_registry=registry)

    result = service.generate_image(
        ImageGenerationRequest(prompt="A cinematic portrait", model="sd15", width=512, height=768)
    )

    assert result.task_id == "prompt-abc"
    assert result.status == "running"
    assert client.submitted_workflow["1"]["inputs"]["ckpt_name"] == "v1-5-pruned-emaonly-fp16.safetensors"
    assert client.submitted_workflow["2"]["inputs"]["text"] == "A cinematic portrait"
    assert client.submitted_workflow["3"]["inputs"]["width"] == 512
    assert client.submitted_workflow["3"]["inputs"]["height"] == 768


def test_image_service_uses_default_dimensions(tmp_path: Path) -> None:
    template_dir = tmp_path / "templates"
    template_dir.mkdir()
    template_path = template_dir / "sd15_text_to_image.json"
    template_path.write_text(json.dumps({"latent": {"inputs": {"width": "{{width}}", "height": "{{height}}"}}}))
    client = FakeComfyUIClient()
    registry = ImageModelRegistry(default_model_id="sd15", template_dir=template_dir)
    service = ImageService(client=client, model_registry=registry)

    service.generate_image(ImageGenerationRequest(prompt="A portrait"))

    assert client.submitted_workflow["latent"]["inputs"] == {"width": 512, "height": 512}


def test_image_service_uses_unique_seed_and_filename_prefix_for_each_submission(tmp_path: Path) -> None:
    template_dir = tmp_path / "templates"
    template_dir.mkdir()
    template_path = template_dir / "sd15_text_to_image.json"
    template_path.write_text(
        json.dumps(
            {
                "5": {"class_type": "KSampler", "inputs": {"seed": 20260710}},
                "7": {"class_type": "SaveImage", "inputs": {"filename_prefix": "AIStudio_SD15"}},
            }
        )
    )
    client = FakeComfyUIClient()
    registry = ImageModelRegistry(default_model_id="sd15", template_dir=template_dir)
    service = ImageService(client=client, model_registry=registry)

    service.generate_image(ImageGenerationRequest(prompt="A portrait"))
    first_seed = client.submitted_workflow["5"]["inputs"]["seed"]
    first_prefix = client.submitted_workflow["7"]["inputs"]["filename_prefix"]

    service.generate_image(ImageGenerationRequest(prompt="A portrait"))
    second_seed = client.submitted_workflow["5"]["inputs"]["seed"]
    second_prefix = client.submitted_workflow["7"]["inputs"]["filename_prefix"]

    assert isinstance(first_seed, int)
    assert isinstance(second_seed, int)
    assert first_seed != second_seed
    assert first_prefix.startswith("AIStudio_SD15_")
    assert second_prefix.startswith("AIStudio_SD15_")
    assert first_prefix != second_prefix


def test_image_service_uses_requested_sdxl_lightning_model(tmp_path: Path) -> None:
    template_dir = tmp_path / "templates"
    template_dir.mkdir()
    (template_dir / "sdxl_lightning_4step_text_to_image.json").write_text(
        json.dumps(
            {
                "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "{{checkpoint}}"}},
                "2": {"class_type": "EmptyLatentImage", "inputs": {"width": "{{width}}", "height": "{{height}}"}},
            }
        )
    )
    client = FakeComfyUIClient()
    registry = ImageModelRegistry(default_model_id="sd15", template_dir=template_dir)
    service = ImageService(client=client, model_registry=registry)

    service.generate_image(ImageGenerationRequest(prompt="A portrait", model="sdxl-lightning-4step"))

    assert client.submitted_workflow["1"]["inputs"]["ckpt_name"] == "sdxl_lightning_4step.safetensors"
    assert client.submitted_workflow["2"]["inputs"] == {"width": 768, "height": 768}


def test_sdxl_lightning_workflow_uses_required_sampler_settings() -> None:
    client = FakeComfyUIClient()
    service = ImageService(
        client=client,
        history_service=WorkflowHistoryService(InMemoryWorkflowHistoryRepository()),
    )

    service.generate_image(ImageGenerationRequest(prompt="A portrait", model="sdxl-lightning-4step"))

    sampler = next(
        node["inputs"]
        for node in client.submitted_workflow.values()
        if node.get("class_type") == "KSampler"
    )
    assert sampler["steps"] == 4
    assert sampler["cfg"] == 1.0
    assert sampler["sampler_name"] == "euler"
    assert sampler["scheduler"] == "sgm_uniform"


def test_image_service_rejects_missing_checkpoint() -> None:
    client = FakeComfyUIClient()
    client.available_checkpoints = set()
    service = ImageService(
        client=client,
        history_service=WorkflowHistoryService(InMemoryWorkflowHistoryRepository()),
    )

    with pytest.raises(ImageCheckpointNotFoundError, match="v1-5-pruned-emaonly-fp16.safetensors"):
        service.generate_image(ImageGenerationRequest(prompt="A portrait", model="sd15"))


def test_image_service_returns_running_when_history_is_not_ready() -> None:
    client = FakeComfyUIClient()
    service = ImageService(client=client)

    status = service.get_generation_status("prompt-abc")

    assert status == ImageGenerationStatus(task_id="prompt-abc", status="running", progress=50, image_url=None)


def test_image_service_returns_completed_with_image_url() -> None:
    client = FakeComfyUIClient()
    client.history = {
        "prompt-abc": {
            "status": {"completed": True, "status_str": "success"},
            "outputs": {
                "7": {
                    "images": [
                        {"filename": "AIStudio_FLUX1_schnell_fp8_00001_.png", "subfolder": "", "type": "output"}
                    ]
                }
            },
        }
    }
    service = ImageService(client=client)

    status = service.get_generation_status("prompt-abc")

    assert status.task_id == "prompt-abc"
    assert status.status == "completed"
    assert status.progress == 100
    assert status.image_url == "/api/v1/images/result/AIStudio_FLUX1_schnell_fp8_00001_.png"


def test_image_service_returns_failed_when_comfyui_reports_error() -> None:
    client = FakeComfyUIClient()
    client.history = {
        "prompt-abc": {
            "status": {"completed": False, "status_str": "error"},
            "outputs": {},
        }
    }
    service = ImageService(client=client)

    status = service.get_generation_status("prompt-abc")

    assert status.task_id == "prompt-abc"
    assert status.status == "failed"
    assert status.progress == 100
    assert status.image_url is None


def test_image_service_reads_result_through_comfyui_http_api() -> None:
    client = FakeComfyUIClient()
    service = ImageService(client=client)

    image = service.get_result_image("result.png")

    assert image.content == b"remote-png"
    assert image.content_type == "image/png"
    assert image.filename == "result.png"


def test_image_service_creates_history_without_internal_workflow_payload(tmp_path: Path) -> None:
    template_dir = tmp_path / "templates"
    template_dir.mkdir()
    (template_dir / "sd15_text_to_image.json").write_text(json.dumps({"save": {"class_type": "SaveImage", "inputs": {"filename_prefix": "AIStudio"}}}))
    client = FakeComfyUIClient()
    history = WorkflowHistoryService(InMemoryWorkflowHistoryRepository())
    service = ImageService(
        client=client,
        model_registry=ImageModelRegistry(default_model_id="sd15", template_dir=template_dir),
        history_service=history,
    )

    result = service.generate_image(ImageGenerationRequest(prompt="A cat", model="sd15", width=512, height=512))
    run = history.get_by_external_task_id(WorkflowType.image_generation, result.task_id)

    assert run.workflow_type == WorkflowType.image_generation
    assert run.runtime == "comfyui"
    assert run.provider == "sd15"
    assert run.status == WorkflowRunStatus.running
    assert run.input_payload == {"model": "sd15", "prompt": "A cat", "width": 512, "height": 512}
    assert "class_type" not in str(run.input_payload)


def test_image_service_updates_history_when_task_completes() -> None:
    client = FakeComfyUIClient()
    client.history = {
        "prompt-abc": {
            "status": {"completed": True, "status_str": "success"},
            "outputs": {"7": {"images": [{"filename": "result.png", "subfolder": "", "type": "output"}]}},
        }
    }
    history = WorkflowHistoryService(InMemoryWorkflowHistoryRepository())
    history.create_image_generation_run(
        external_task_id="prompt-abc", model="sd15", prompt="A cat", width=512, height=512
    )
    service = ImageService(client=client, history_service=history)

    status = service.get_generation_status("prompt-abc")
    run = history.get_by_external_task_id(WorkflowType.image_generation, "prompt-abc")

    assert status.status == "completed"
    assert run.status == WorkflowRunStatus.succeeded
    assert run.result_file_id == "image:result.png"
    assert run.output_payload == {"filename": "result.png", "image_url": "/api/v1/images/result/result.png"}
    assert run.completed_at is not None


def test_image_service_updates_history_when_task_fails() -> None:
    client = FakeComfyUIClient()
    client.history = {"prompt-abc": {"status": {"completed": False, "status_str": "error"}, "outputs": {}}}
    history = WorkflowHistoryService(InMemoryWorkflowHistoryRepository())
    history.create_image_generation_run(
        external_task_id="prompt-abc", model="sd15", prompt="A cat", width=512, height=512
    )
    service = ImageService(client=client, history_service=history)

    status = service.get_generation_status("prompt-abc")
    run = history.get_by_external_task_id(WorkflowType.image_generation, "prompt-abc")

    assert status.status == "failed"
    assert run.status == WorkflowRunStatus.failed
    assert run.error_code == "COMFYUI_TASK_FAILED"
    assert run.completed_at is not None
