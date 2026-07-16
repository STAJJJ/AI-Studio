from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[3]


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

    facefusion_project_path: Path = Field(default=Path("/3241903007/workstation/LYJ/FaceFusion/facefusion"))
    facefusion_python_path: str = Field(default="/opt/conda/envs/df/bin/python")
    facefusion_execution_provider: str = Field(default="cpu")
    facefusion_device_id: int = Field(default=0)
    facefusion_timeout_seconds: int = Field(default=300)

    default_image_model: str = Field(default="sd15")
    runtime_gpu_name: str = Field(default="Apple Silicon MPS")
    comfyui_base_url: str = Field(default="http://127.0.0.1:8188")
    comfyui_timeout_seconds: int = Field(default=120)
    comfyui_output_dir: Path = Field(default=Path("/Users/lyj/WorkStation/Project/ComfyUI/output"))

    llm_base_url: str = Field(default="https://ark.cn-beijing.volces.com/api/v3")
    llm_api_key: str = Field(default="")
    llm_default_model: str = Field(default="deepseek")
    llm_timeout_seconds: int = Field(default=60)
    llm_max_context_messages: int = Field(default=20)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="AI_STUDIO_",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
