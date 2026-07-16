import socket
from urllib.error import HTTPError, URLError
from urllib.request import Request

import pytest

from app.core.config import Settings
from app.schemas.chat import ChatCompletionRequest
from app.services.llm.base import (
    LLMAuthenticationError,
    LLMConfigurationError,
    LLMRateLimitError,
    LLMTimeoutError,
)
import app.services.llm.clients.deepseek_client as deepseek_client_module
from app.services.llm.clients.deepseek_client import DeepSeekClient


class FakeResponse:
    def __init__(self, payload: bytes = b"", lines: list[bytes] | None = None, status: int = 200) -> None:
        self.payload = payload
        self.lines = lines or []
        self.status = status

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        return None

    def read(self) -> bytes:
        return self.payload

    def __iter__(self):
        return iter(self.lines)


def make_settings(api_key: str = "test-key") -> Settings:
    return Settings(
        llm_base_url="https://ark.example.test/api/v3",
        llm_api_key=api_key,
        llm_default_model="ep-deepseek",
        llm_timeout_seconds=12,
    )


def make_request(stream: bool = False) -> ChatCompletionRequest:
    return ChatCompletionRequest(
        model="deepseek",
        messages=[{"role": "user", "content": "hello"}],
        temperature=0.5,
        max_tokens=128,
        stream=stream,
    )


def test_deepseek_generate_calls_openai_compatible_api_without_exposing_endpoint_model() -> None:
    captured: dict[str, Request] = {}

    def transport(request: Request, timeout: int) -> FakeResponse:
        captured["request"] = request
        captured["timeout"] = timeout
        return FakeResponse(
            b'{"model":"ep-deepseek","choices":[{"index":0,"message":{"role":"assistant","content":"hello back"},"finish_reason":"stop"}],"usage":{"prompt_tokens":1,"completion_tokens":2,"total_tokens":3}}'
        )

    client = DeepSeekClient(settings=make_settings(), transport=transport)

    response = client.generate(make_request())

    assert response.model == "deepseek"
    assert response.choices[0].message.content == "hello back"
    assert captured["request"].full_url == "https://ark.example.test/api/v3/chat/completions"
    assert captured["request"].get_header("Authorization") == "Bearer test-key"
    assert captured["timeout"] == 12
    assert b'"model":"ep-deepseek"' in captured["request"].data


def test_deepseek_default_transport_passes_timeout_as_keyword(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_urlopen(request: Request, *, timeout: int) -> FakeResponse:
        captured["request"] = request
        captured["timeout"] = timeout
        return FakeResponse(
            b'{"choices":[{"index":0,"message":{"role":"assistant","content":"ok"},"finish_reason":"stop"}],"usage":{"prompt_tokens":1,"completion_tokens":1,"total_tokens":2}}'
        )

    monkeypatch.setattr(deepseek_client_module, "urlopen", fake_urlopen)
    client = DeepSeekClient(settings=make_settings())

    response = client.generate(make_request())

    assert response.choices[0].message.content == "ok"
    assert captured["timeout"] == 12


def test_deepseek_stream_generate_yields_real_streaming_deltas() -> None:
    def transport(request: Request, timeout: int) -> FakeResponse:
        return FakeResponse(
            lines=[
                b'data: {"choices":[{"delta":{"content":"hello"}}]}\n',
                b'data: {"choices":[{"delta":{"content":" world"}}]}\n',
                b"data: [DONE]\n",
            ]
        )

    client = DeepSeekClient(settings=make_settings(), transport=transport)

    assert list(client.stream_generate(make_request(stream=True))) == ["hello", " world"]


def test_deepseek_requires_api_key() -> None:
    client = DeepSeekClient(settings=make_settings(api_key=""))

    with pytest.raises(LLMConfigurationError, match="DeepSeek API Key 未配置"):
        client.generate(make_request())


def test_deepseek_maps_authentication_failure() -> None:
    def transport(request: Request, timeout: int) -> FakeResponse:
        raise HTTPError(request.full_url, 401, "Unauthorized", hdrs=None, fp=None)

    client = DeepSeekClient(settings=make_settings(), transport=transport)

    with pytest.raises(LLMAuthenticationError, match="模型服务认证失败"):
        client.generate(make_request())


def test_deepseek_maps_rate_limit_failure() -> None:
    def transport(request: Request, timeout: int) -> FakeResponse:
        raise HTTPError(request.full_url, 429, "Too Many Requests", hdrs=None, fp=None)

    client = DeepSeekClient(settings=make_settings(), transport=transport)

    with pytest.raises(LLMRateLimitError, match="请求过于频繁"):
        client.generate(make_request())


def test_deepseek_maps_timeout_failure() -> None:
    def transport(request: Request, timeout: int) -> FakeResponse:
        raise URLError(socket.timeout("timed out"))

    client = DeepSeekClient(settings=make_settings(), transport=transport)

    with pytest.raises(LLMTimeoutError, match="模型服务响应超时"):
        client.generate(make_request())
