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

    assert [model.id for model in models] == ["sd15", "sdxl-lightning-4step"]
    assert {model.id: model.name for model in models} == {
        "sd15": "Stable Diffusion 1.5",
        "sdxl-lightning-4step": "SDXL Lightning 4-Step",
    }


def test_registry_configures_checkpoints_without_absolute_paths() -> None:
    registry = ImageModelRegistry(
        default_model_id="sd15",
        sd15_checkpoint="custom-sd15.safetensors",
        sdxl_lightning_checkpoint="custom-lightning.safetensors",
    )

    assert registry.get_model("sd15").checkpoint == "custom-sd15.safetensors"
    assert registry.get_model("sdxl-lightning-4step").checkpoint == "custom-lightning.safetensors"


def test_registry_rejects_removed_flux_model() -> None:
    registry = ImageModelRegistry(default_model_id="sd15")

    with pytest.raises(UnknownImageModelError, match="Unsupported image model: flux"):
        registry.get_model("flux")


def test_registry_rejects_unknown_model() -> None:
    registry = ImageModelRegistry(default_model_id="sd15")

    with pytest.raises(UnknownImageModelError):
        registry.get_model("unknown")


def test_registry_rejects_empty_model_instead_of_using_default() -> None:
    registry = ImageModelRegistry(default_model_id="sd15")

    with pytest.raises(UnknownImageModelError, match="Unsupported image model"):
        registry.get_model("")


def test_registry_resolves_workflow_template_path() -> None:
    registry = ImageModelRegistry(default_model_id="sd15", template_dir=Path("/tmp/templates"))

    assert registry.get_workflow_path("sd15") == Path("/tmp/templates/sd15_text_to_image.json")


def test_registry_maps_sdxl_lightning_workflow() -> None:
    registry = ImageModelRegistry(default_model_id="sd15", template_dir=Path("/tmp/templates"))

    assert registry.get_workflow_path("sdxl-lightning-4step") == Path(
        "/tmp/templates/sdxl_lightning_4step_text_to_image.json"
    )
