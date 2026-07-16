from collections.abc import Iterator

from app.core.config import get_settings
from app.schemas.chat import ChatCompletionRequest, ChatCompletionResponse, ChatMessage
from app.services.llm.gateway import LLMGateway, llm_gateway
from app.services.llm.role_registry import RoleRegistry, role_registry


class ChatValidationError(ValueError):
    pass


class ChatService:
    def __init__(
        self,
        gateway: LLMGateway,
        roles: RoleRegistry = role_registry,
        max_context_messages: int | None = None,
    ) -> None:
        self._gateway = gateway
        self._roles = roles
        self._max_context_messages = max_context_messages or get_settings().llm_max_context_messages

    def create_completion(self, role_id: str, request: ChatCompletionRequest) -> ChatCompletionResponse:
        prepared_request = self._prepare_request(role_id=role_id, request=request)
        return self._gateway.chat(prepared_request)

    def stream_completion(self, role_id: str, request: ChatCompletionRequest) -> Iterator[str]:
        prepared_request = self._prepare_request(role_id=role_id, request=request)
        return self._gateway.stream_chat(prepared_request)

    def _prepare_request(self, role_id: str, request: ChatCompletionRequest) -> ChatCompletionRequest:
        role = self._roles.get_role(role_id)
        messages = self._sanitize_messages(request.messages)
        if not any(message.role == "user" for message in messages):
            raise ChatValidationError("At least one non-empty user message is required.")

        trimmed_messages = self._trim_context(messages)
        return request.model_copy(
            update={
                "role_id": role.id,
                "messages": [ChatMessage(role="system", content=role.system_prompt), *trimmed_messages],
            }
        )

    def _sanitize_messages(self, messages: list[ChatMessage]) -> list[ChatMessage]:
        sanitized: list[ChatMessage] = []
        for message in messages:
            content = message.content.strip()
            if message.role == "system" or not content:
                continue
            if message.role not in ("user", "assistant"):
                continue
            sanitized.append(ChatMessage(role=message.role, content=content))
        return sanitized

    def _trim_context(self, messages: list[ChatMessage]) -> list[ChatMessage]:
        trimmed = messages[-self._max_context_messages :]
        while trimmed and trimmed[0].role == "assistant":
            trimmed = trimmed[1:]
        return trimmed


chat_service = ChatService(gateway=llm_gateway)
