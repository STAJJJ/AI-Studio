from collections.abc import Iterator

from app.schemas.chat import (
    ChatCompletionChoice,
    ChatCompletionMessage,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionUsage,
)
from app.services.llm.base import BaseLLMClient


class OpenAIClient(BaseLLMClient):
    model_id = "gpt"
    provider_name = "openai"

    def generate(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        return ChatCompletionResponse(
            model=request.model,
            choices=[
                ChatCompletionChoice(
                    index=0,
                    message=ChatCompletionMessage(content="Hello AI Studio"),
                    finish_reason="stop",
                )
            ],
            usage=ChatCompletionUsage(
                prompt_tokens=sum(len(message.content.split()) for message in request.messages),
                completion_tokens=3,
                total_tokens=sum(len(message.content.split()) for message in request.messages) + 3,
            ),
        )

    def stream_generate(self, request: ChatCompletionRequest) -> Iterator[str]:
        yield "Hello"
        yield " AI"
        yield " Studio"

    def health_check(self) -> bool:
        return True
