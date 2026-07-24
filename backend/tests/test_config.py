from app.core.config import Settings


def test_comfyui_base_url_uses_new_standard_environment_variable(monkeypatch) -> None:
    monkeypatch.setenv("COMFYUI_BASE_URL", "http://127.0.0.1:18188/")
    monkeypatch.setenv("AI_STUDIO_COMFYUI_BASE_URL", "http://legacy.invalid:8188")

    settings = Settings(_env_file=None)

    assert settings.comfyui_base_url == "http://127.0.0.1:18188/"


def test_comfyui_base_url_accepts_deprecated_environment_variable(monkeypatch) -> None:
    monkeypatch.delenv("COMFYUI_BASE_URL", raising=False)
    monkeypatch.setenv("AI_STUDIO_COMFYUI_BASE_URL", "http://127.0.0.1:8188")

    settings = Settings(_env_file=None)

    assert settings.comfyui_base_url == "http://127.0.0.1:8188"
