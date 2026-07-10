import json
from pathlib import Path

from app.services.image_service import ImageGenerationRequest, ImageService


class FakeComfyUIClient:
    def __init__(self) -> None:
        self.submitted_workflow = None

    def submit_workflow(self, workflow):
        self.submitted_workflow = workflow
        return "prompt-abc"


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
