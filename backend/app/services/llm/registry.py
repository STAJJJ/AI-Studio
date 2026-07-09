from app.services.llm.base import BaseLLMClient
from app.services.llm.clients import DeepSeekClient, OpenAIClient, QwenClient


class LLMClientNotFoundError(ValueError):
    pass


class LLMRegistry:
    def __init__(self) -> None:
        self._clients: dict[str, BaseLLMClient] = {}

    def register(self, client: BaseLLMClient) -> None:
        self._clients[client.model_id] = client

    def get_client(self, model: str) -> BaseLLMClient:
        try:
            return self._clients[model]
        except KeyError as exc:
            raise LLMClientNotFoundError(f"Unsupported LLM model: {model}") from exc

    def list_clients(self) -> list[BaseLLMClient]:
        return list(self._clients.values())


def build_default_registry() -> LLMRegistry:
    registry = LLMRegistry()
    registry.register(OpenAIClient())
    registry.register(QwenClient())
    registry.register(DeepSeekClient())
    return registry


llm_registry = build_default_registry()
