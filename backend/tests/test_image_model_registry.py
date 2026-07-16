from pathlib import Path

import pytest

from app.services.comfyui.model_registry import ImageModelRegistry, UnknownImageModelError


def test_registry_returns_default_sd15_model() -> None:
    registry = ImageModelRegistry(default_model_id="sd15")

    model = registry.get_default_model()

    assert model.id == "sd15"
    assert model.name == "Stable Diffusion 1.5"
    assert model.checkpoint == "v1-5-pruned-emaonly-fp16.safetensors"
    assert model.workflow == "sd15_text_to_image.json"
    assert model.width == 512
    assert model.height == 512


def test_registry_lists_supported_models() -> None:
    registry = ImageModelRegistry(default_model_id="sd15")

    models = registry.list_models()

    assert [model.id for model in models] == ["sd15", "flux"]
    assert {model.id: model.name for model in models} == {
        "sd15": "Stable Diffusion 1.5",
        "flux": "FLUX.1 Schnell FP8",
    }


def test_registry_rejects_unknown_model() -> None:
    registry = ImageModelRegistry(default_model_id="sd15")

    with pytest.raises(UnknownImageModelError):
        registry.get_model("unknown")


def test_registry_resolves_workflow_template_path() -> None:
    registry = ImageModelRegistry(default_model_id="sd15", template_dir=Path("/tmp/templates"))

    assert registry.get_workflow_path("sd15") == Path("/tmp/templates/sd15_text_to_image.json")
