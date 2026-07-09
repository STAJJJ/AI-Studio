from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_list_models_returns_supported_llm_models() -> None:
    response = client.get("/api/v1/models")

    assert response.status_code == 200
    payload = response.json()
    assert payload["object"] == "list"
    model_ids = {model["id"] for model in payload["data"]}
    assert {"gpt", "qwen", "deepseek"}.issubset(model_ids)


def test_chat_completions_returns_openai_style_mock_response() -> None:
    response = client.post(
        "/api/v1/chat/completions",
        json={
            "model": "qwen",
            "messages": [
                {"role": "user", "content": "Hello"},
            ],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["object"] == "chat.completion"
    assert payload["model"] == "qwen"
    assert payload["choices"][0]["index"] == 0
    assert payload["choices"][0]["message"] == {
        "role": "assistant",
        "content": "Hello AI Studio",
    }
    assert payload["choices"][0]["finish_reason"] == "stop"
    assert payload["usage"]["total_tokens"] >= payload["usage"]["prompt_tokens"]


def test_chat_completions_rejects_unsupported_model() -> None:
    response = client.post(
        "/api/v1/chat/completions",
        json={
            "model": "unknown-model",
            "messages": [
                {"role": "user", "content": "Hello"},
            ],
        },
    )

    assert response.status_code == 400
    assert "Unsupported LLM model" in response.json()["detail"]
