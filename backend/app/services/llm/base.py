from abc import ABC, abstractmethod
from collections.abc import Iterator

from app.schemas.chat import ChatCompletionRequest, ChatCompletionResponse, ModelInfo


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
