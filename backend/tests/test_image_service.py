import json
from pathlib import Path

from app.services.comfyui.model_registry import ImageModelRegistry
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


def test_image_service_uses_requested_flux_model(tmp_path: Path) -> None:
    template_dir = tmp_path / "templates"
    template_dir.mkdir()
    (template_dir / "flux1_schnell_fp8_text_to_image.json").write_text(
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

    service.generate_image(ImageGenerationRequest(prompt="A portrait", model="flux"))

    assert client.submitted_workflow["1"]["inputs"]["ckpt_name"] == "flux1-schnell-fp8.safetensors"
    assert client.submitted_workflow["2"]["inputs"] == {"width": 1024, "height": 1024}


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


def test_image_service_resolves_output_file_without_copying(tmp_path: Path) -> None:
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    image_path = output_dir / "result.png"
    image_path.write_bytes(b"png")
    client = FakeComfyUIClient()
    service = ImageService(client=client, output_dir=output_dir)

    assert service.get_result_path("result.png") == image_path
