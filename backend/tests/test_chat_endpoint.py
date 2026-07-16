from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_get_chat_roles_returns_public_role_metadata() -> None:
    response = client.get("/api/v1/chat/roles")

    assert response.status_code == 200
    payload = response.json()
    assert {role["id"] for role in payload["roles"]} >= {
        "general_assistant",
        "aigc_engineer",
        "interview_coach",
    }
    assert "system_prompt" not in payload["roles"][0]


def test_chat_completion_rejects_invalid_role_id() -> None:
    response = client.post(
        "/api/v1/chat/completions",
        json={
            "role_id": "missing",
            "model": "deepseek",
            "messages": [{"role": "user", "content": "hello"}],
        },
    )

    assert response.status_code == 400
    assert "Unsupported chat role" in response.json()["detail"]


def test_chat_completion_rejects_empty_message() -> None:
    response = client.post(
        "/api/v1/chat/completions",
        json={
            "role_id": "general_assistant",
            "model": "deepseek",
            "messages": [{"role": "user", "content": "   "}],
        },
    )

    assert response.status_code == 422
    assert "non-empty user message" in response.json()["detail"]


def test_chat_completion_stream_returns_sse_events() -> None:
    with client.stream(
        "POST",
        "/api/v1/chat/completions",
        json={
            "role_id": "general_assistant",
            "model": "qwen",
            "messages": [{"role": "user", "content": "hello"}],
            "stream": True,
        },
    ) as response:
        body = response.read().decode()

    assert response.status_code == 200
    assert 'data: {"type":"delta","content":"Hello"}' in body
    assert 'data: {"type":"done"}' in body
    assert "data: [DONE]" in body
