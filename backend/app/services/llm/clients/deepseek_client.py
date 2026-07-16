import json
import socket
from collections.abc import Callable, Iterator
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.core.config import Settings, get_settings
from app.schemas.chat import (
    ChatCompletionChoice,
    ChatCompletionMessage,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionUsage,
)
from app.services.llm.base import (
    BaseLLMClient,
    LLMAuthenticationError,
    LLMConfigurationError,
    LLMProviderError,
    LLMRateLimitError,
    LLMTimeoutError,
    LLMUpstreamError,
)


Transport = Callable[[Request, int], Any]


class DeepSeekClient(BaseLLMClient):
    model_id = "deepseek"
    provider_name = "deepseek"

    def __init__(self, settings: Settings | None = None, transport: Transport | None = None) -> None:
        self._settings = settings or get_settings()
        self._transport = transport or (lambda request, timeout: urlopen(request, timeout=timeout))

    def generate(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        payload = self._build_payload(request, stream=False)
        response_payload = self._request_json(payload)
        return self._parse_completion_response(response_payload)

    def stream_generate(self, request: ChatCompletionRequest) -> Iterator[str]:
        payload = self._build_payload(request, stream=True)
        with self._open_request(payload) as response:
            for line in response:
                text = line.decode("utf-8").strip()
                if not text or not text.startswith("data:"):
                    continue
                data = text.removeprefix("data:").strip()
                if data == "[DONE]":
                    break
                chunk = json.loads(data)
                for choice in chunk.get("choices", []):
                    content = choice.get("delta", {}).get("content")
                    if content:
                        yield content

    def health_check(self) -> bool:
        return bool(self._settings.llm_api_key and self._settings.llm_default_model)

    def _build_payload(self, request: ChatCompletionRequest, stream: bool) -> bytes:
        body: dict[str, Any] = {
            "model": self._settings.llm_default_model,
            "messages": [message.model_dump() for message in request.messages],
            "stream": stream,
        }
        if request.temperature is not None:
            body["temperature"] = request.temperature
        if request.max_tokens is not None:
            body["max_tokens"] = request.max_tokens
        return json.dumps(body, ensure_ascii=False, separators=(",", ":")).encode("utf-8")

    def _request_json(self, payload: bytes) -> dict[str, Any]:
        with self._open_request(payload) as response:
            return json.loads(response.read().decode("utf-8"))

    def _open_request(self, payload: bytes) -> Any:
        self._ensure_configured()
        request = Request(
            url=f"{self._settings.llm_base_url.rstrip('/')}/chat/completions",
            data=payload,
            headers={
                "Authorization": f"Bearer {self._settings.llm_api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            return self._transport(request, self._settings.llm_timeout_seconds)
        except HTTPError as exc:
            self._raise_http_error(exc)
        except URLError as exc:
            if isinstance(exc.reason, socket.timeout):
                raise LLMTimeoutError("模型服务响应超时，请稍后重试") from exc
            raise LLMUpstreamError("模型服务网络不可用，请检查网络或上游服务") from exc
        except socket.timeout as exc:
            raise LLMTimeoutError("模型服务响应超时，请稍后重试") from exc

    def _ensure_configured(self) -> None:
        if not self._settings.llm_api_key:
            raise LLMConfigurationError("DeepSeek API Key 未配置")
        if not self._settings.llm_base_url or not self._settings.llm_default_model:
            raise LLMConfigurationError("DeepSeek 模型服务配置不完整")

    def _raise_http_error(self, exc: HTTPError) -> None:
        if exc.code in (401, 403):
            raise LLMAuthenticationError("模型服务认证失败") from exc
        if exc.code == 429:
            raise LLMRateLimitError("请求过于频繁，请稍后再试") from exc
        if exc.code == 404:
            raise LLMUpstreamError("模型或 Endpoint ID 不存在") from exc
        raise LLMUpstreamError("模型服务返回错误") from exc

    def _parse_completion_response(self, payload: dict[str, Any]) -> ChatCompletionResponse:
        choices = [
            ChatCompletionChoice(
                index=choice.get("index", index),
                message=ChatCompletionMessage(content=choice.get("message", {}).get("content", "")),
                finish_reason=choice.get("finish_reason") or "stop",
            )
            for index, choice in enumerate(payload.get("choices", []))
        ]
        usage_payload = payload.get("usage", {})
        usage = ChatCompletionUsage(
            prompt_tokens=usage_payload.get("prompt_tokens", 0),
            completion_tokens=usage_payload.get("completion_tokens", 0),
            total_tokens=usage_payload.get("total_tokens", 0),
        )
        return ChatCompletionResponse(model=self.model_id, choices=choices, usage=usage)
