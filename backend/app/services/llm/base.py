from abc import ABC, abstractmethod
from collections.abc import Iterator

from app.schemas.chat import ChatCompletionRequest, ChatCompletionResponse, ModelInfo


class LLMProviderError(RuntimeError):
    status_code = 502


class LLMConfigurationError(LLMProviderError):
    status_code = 500


class LLMAuthenticationError(LLMProviderError):
    status_code = 401


class LLMRateLimitError(LLMProviderError):
    status_code = 429


class LLMTimeoutError(LLMProviderError):
    status_code = 504


class LLMUpstreamError(LLMProviderError):
    status_code = 502


class BaseLLMClient(ABC):
    model_id: str
    provider_name: str

    @abstractmethod
    def generate(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        """Generate a non-streaming chat completion."""

    @abstractmethod
    def stream_generate(self, request: ChatCompletionRequest) -> Iterator[str]:
        """Generate a streaming chat completion."""

    @abstractmethod
    def health_check(self) -> bool:
        """Return whether the provider client is available."""

    def model_info(self) -> ModelInfo:
        return ModelInfo(id=self.model_id, owned_by=self.provider_name)
