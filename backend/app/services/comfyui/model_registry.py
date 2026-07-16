from dataclasses import dataclass
from pathlib import Path


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


MODELS: dict[str, ImageModelConfig] = {
    "sd15": ImageModelConfig(
        id="sd15",
        name="Stable Diffusion 1.5",
        checkpoint="v1-5-pruned-emaonly-fp16.safetensors",
        workflow="sd15_text_to_image.json",
        width=512,
        height=512,
    ),
    "flux": ImageModelConfig(
        id="flux",
        name="FLUX.1 Schnell FP8",
        checkpoint="flux1-schnell-fp8.safetensors",
        workflow="flux1_schnell_fp8_text_to_image.json",
        width=1024,
        height=1024,
    ),
}


class ImageModelRegistry:
    def __init__(
        self,
        default_model_id: str = "sd15",
        template_dir: Path = TEMPLATE_DIR,
        models: dict[str, ImageModelConfig] | None = None,
    ) -> None:
        self._models = models or MODELS
        self._default_model_id = default_model_id
        self._template_dir = template_dir
        self.get_model(default_model_id)

    @property
    def default_model_id(self) -> str:
        return self._default_model_id

    def get_model(self, model_id: str | None) -> ImageModelConfig:
        resolved_model_id = model_id or self._default_model_id
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
