from app.schemas.chat import ChatCompletionRequest, ChatCompletionResponse, ModelListResponse
from app.services.llm.registry import LLMRegistry, llm_registry


class LLMGateway:
    def __init__(self, registry: LLMRegistry) -> None:
        self._registry = registry

    def chat(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        client = self._registry.get_client(request.model)
        return client.generate(request)

    def stream_chat(self, request: ChatCompletionRequest) -> object:
        client = self._registry.get_client(request.model)
        return client.stream_generate(request)

    def list_models(self) -> ModelListResponse:
        return ModelListResponse(data=[client.model_info() for client in self._registry.list_clients()])


llm_gateway = LLMGateway(llm_registry)
