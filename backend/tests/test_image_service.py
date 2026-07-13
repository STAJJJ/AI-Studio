import json
from pathlib import Path

from app.services.image_service import ImageGenerationRequest, ImageGenerationStatus, ImageService


class FakeComfyUIClient:
    def __init__(self) -> None:
        self.submitted_workflow = None
        self.history = {}

    def submit_workflow(self, workflow):
        self.submitted_workflow = workflow
        return "prompt-abc"

    def get_history(self, task_id):
        return self.history


def test_image_service_loads_template_and_submits_rendered_workflow(tmp_path: Path) -> None:
    template_path = tmp_path / "workflow.json"
    template_path.write_text(
        json.dumps(
            {
                "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "flux1-schnell-fp8.safetensors"}},
                "2": {"class_type": "CLIPTextEncode", "inputs": {"text": "{{prompt}}"}},
                "3": {"class_type": "EmptyLatentImage", "inputs": {"width": "{{width}}", "height": "{{height}}", "batch_size": 1}},
            }
        )
    )
    client = FakeComfyUIClient()
    service = ImageService(client=client, workflow_template_path=template_path)

    result = service.generate_image(
        ImageGenerationRequest(prompt="A cinematic portrait", width=1024, height=768)
    )

    assert result.task_id == "prompt-abc"
    assert result.status == "running"
    assert client.submitted_workflow["2"]["inputs"]["text"] == "A cinematic portrait"
    assert client.submitted_workflow["3"]["inputs"]["width"] == 1024
    assert client.submitted_workflow["3"]["inputs"]["height"] == 768


def test_image_service_uses_default_dimensions(tmp_path: Path) -> None:
    template_path = tmp_path / "workflow.json"
    template_path.write_text(json.dumps({"latent": {"inputs": {"width": "{{width}}", "height": "{{height}}"}}}))
    client = FakeComfyUIClient()
    service = ImageService(client=client, workflow_template_path=template_path)

    service.generate_image(ImageGenerationRequest(prompt="A portrait"))

    assert client.submitted_workflow["latent"]["inputs"] == {"width": 1024, "height": 1024}


def test_image_service_returns_running_when_history_is_not_ready(tmp_path: Path) -> None:
    template_path = tmp_path / "workflow.json"
    template_path.write_text(json.dumps({}))
    client = FakeComfyUIClient()
    service = ImageService(client=client, workflow_template_path=template_path)

    status = service.get_generation_status("prompt-abc")

    assert status == ImageGenerationStatus(task_id="prompt-abc", status="running", progress=50, image_url=None)


def test_image_service_returns_completed_with_image_url(tmp_path: Path) -> None:
    template_path = tmp_path / "workflow.json"
    template_path.write_text(json.dumps({}))
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
    service = ImageService(client=client, workflow_template_path=template_path)

    status = service.get_generation_status("prompt-abc")

    assert status.task_id == "prompt-abc"
    assert status.status == "completed"
    assert status.progress == 100
    assert status.image_url == "/api/v1/images/result/AIStudio_FLUX1_schnell_fp8_00001_.png"


def test_image_service_returns_failed_when_comfyui_reports_error(tmp_path: Path) -> None:
    template_path = tmp_path / "workflow.json"
    template_path.write_text(json.dumps({}))
    client = FakeComfyUIClient()
    client.history = {
        "prompt-abc": {
            "status": {"completed": False, "status_str": "error"},
            "outputs": {},
        }
    }
    service = ImageService(client=client, workflow_template_path=template_path)

    status = service.get_generation_status("prompt-abc")

    assert status.task_id == "prompt-abc"
    assert status.status == "failed"
    assert status.progress == 100
    assert status.image_url is None


def test_image_service_resolves_output_file_without_copying(tmp_path: Path) -> None:
    template_path = tmp_path / "workflow.json"
    template_path.write_text(json.dumps({}))
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    image_path = output_dir / "result.png"
    image_path.write_bytes(b"png")
    client = FakeComfyUIClient()
    service = ImageService(client=client, workflow_template_path=template_path, output_dir=output_dir)

    assert service.get_result_path("result.png") == image_path
