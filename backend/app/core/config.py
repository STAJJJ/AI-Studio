from functools import lru_cache
from pathlib import Path
import sys
from typing import Literal

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_SD15_CHECKPOINT = "v1-5-pruned-emaonly-fp16.safetensors"
DEFAULT_SDXL_LIGHTNING_CHECKPOINT = "sdxl_lightning_4step.safetensors"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    app_name: str = Field(default="AI Studio", description="FastAPI application name.")
    api_v1_prefix: str = Field(default="/api/v1", description="Versioned API prefix.")
    environment: Literal["local", "development", "staging", "production"] = "local"
    debug: bool = False
    log_level: str = "INFO"
    max_file_size_bytes: int = Field(default=10 * 1024 * 1024, description="Maximum upload size in bytes.")
    allowed_mime_types: set[str] = Field(default={"image/jpeg", "image/png", "image/webp"})
    upload_dir: Path = Field(default=PROJECT_ROOT / "data" / "uploads")
    output_dir: Path = Field(default=PROJECT_ROOT / "data" / "outputs")
    mock_executor_delay_seconds: float = 2.0
    history_backend: Literal["memory", "sqlite"] = "sqlite"
    database_url: str = Field(default=f"sqlite:///{PROJECT_ROOT / 'data' / 'ai_studio.db'}")

    facefusion_project_path: Path = Field(default=PROJECT_ROOT.parent / "FaceFusion" / "facefusion")
    facefusion_python_path: str = Field(default=sys.executable)
    facefusion_execution_provider: str = Field(default="cpu")
    facefusion_device_id: int = Field(default=0)
    facefusion_timeout_seconds: int = Field(default=300)

    default_image_model: str = Field(default="sd15")
    runtime_gpu_name: str = Field(default="Apple Silicon MPS")
    sd15_checkpoint: str = Field(default=DEFAULT_SD15_CHECKPOINT)
    sdxl_lightning_checkpoint: str = Field(default=DEFAULT_SDXL_LIGHTNING_CHECKPOINT)
    comfyui_base_url: str = Field(
        default="http://127.0.0.1:8188",
        validation_alias=AliasChoices("COMFYUI_BASE_URL", "AI_STUDIO_COMFYUI_BASE_URL"),
    )
    comfyui_timeout_seconds: int = Field(default=120)
    comfyui_output_dir: Path | None = Field(
        default=None,
        description="Deprecated compatibility setting; image results are fetched through the ComfyUI HTTP API.",
    )

    llm_base_url: str = Field(default="https://ark.cn-beijing.volces.com/api/v3")
    llm_api_key: str = Field(default="")
    llm_default_model: str = Field(default="deepseek")
    llm_timeout_seconds: int = Field(default=60)
    llm_max_context_messages: int = Field(default=20)

    model_config = SettingsConfigDict(
        env_file=(PROJECT_ROOT / ".env", ".env"),
        env_file_encoding="utf-8",
        env_prefix="AI_STUDIO_",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
