from dataclasses import dataclass
from pathlib import Path

from app.core.config import DEFAULT_SD15_CHECKPOINT, DEFAULT_SDXL_LIGHTNING_CHECKPOINT


TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"


class UnknownImageModelError(ValueError):
    pass


@dataclass(frozen=True)
class ImageModelConfig:
    id: str
    name: str
    checkpoint: str
    workflow: str
    width: int
    height: int


def _build_models(sd15_checkpoint: str, sdxl_lightning_checkpoint: str) -> dict[str, ImageModelConfig]:
    return {
        "sd15": ImageModelConfig(
            id="sd15",
            name="Stable Diffusion 1.5",
            checkpoint=sd15_checkpoint,
            workflow="sd15_text_to_image.json",
            width=512,
            height=512,
        ),
        "sdxl-lightning-4step": ImageModelConfig(
            id="sdxl-lightning-4step",
            name="SDXL Lightning 4-Step",
            checkpoint=sdxl_lightning_checkpoint,
            workflow="sdxl_lightning_4step_text_to_image.json",
            width=768,
            height=768,
        ),
    }


class ImageModelRegistry:
    def __init__(
        self,
        default_model_id: str = "sd15",
        template_dir: Path = TEMPLATE_DIR,
        models: dict[str, ImageModelConfig] | None = None,
        sd15_checkpoint: str = DEFAULT_SD15_CHECKPOINT,
        sdxl_lightning_checkpoint: str = DEFAULT_SDXL_LIGHTNING_CHECKPOINT,
    ) -> None:
        self._models = models if models is not None else _build_models(sd15_checkpoint, sdxl_lightning_checkpoint)
        self._default_model_id = default_model_id
        self._template_dir = template_dir
        self.get_model(default_model_id)

    @property
    def default_model_id(self) -> str:
        return self._default_model_id

    def get_model(self, model_id: str | None) -> ImageModelConfig:
        resolved_model_id = self._default_model_id if model_id is None else model_id
        try:
            return self._models[resolved_model_id]
        except KeyError as exc:
            raise UnknownImageModelError(f"Unsupported image model: {resolved_model_id}") from exc

    def get_default_model(self) -> ImageModelConfig:
        return self.get_model(self._default_model_id)

    def list_models(self) -> list[ImageModelConfig]:
        return list(self._models.values())

    def get_workflow_path(self, model_id: str | None) -> Path:
        model = self.get_model(model_id)
        return self._template_dir / model.workflow
