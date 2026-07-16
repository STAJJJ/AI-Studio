import json
from collections.abc import Iterator

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse

from app.schemas.chat import ChatCompletionRequest, ChatCompletionResponse, ChatRoleListResponse, ModelListResponse
from app.services.chat_service import ChatValidationError, chat_service
from app.services.llm.base import LLMProviderError
from app.services.llm.gateway import llm_gateway
from app.services.llm.registry import LLMClientNotFoundError
from app.services.llm.role_registry import RoleNotFoundError, role_registry

router = APIRouter(tags=["LLM"])


@router.get("/models", response_model=ModelListResponse)
def list_models() -> ModelListResponse:
    return llm_gateway.list_models()


@router.get("/chat/roles", response_model=ChatRoleListResponse)
def list_chat_roles() -> ChatRoleListResponse:
    return ChatRoleListResponse(roles=role_registry.list_public_roles())


@router.post("/chat/completions", response_model=None)
def create_chat_completion(request: ChatCompletionRequest):
    try:
        if request.stream:
            return StreamingResponse(
                _sse_events(chat_service.stream_completion(role_id=request.role_id, request=request)),
                media_type="text/event-stream",
            )
        return chat_service.create_completion(role_id=request.role_id, request=request)
    except LLMClientNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except RoleNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except ChatValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except LLMProviderError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


def _sse_events(chunks: Iterator[str]) -> Iterator[str]:
    try:
        for chunk in chunks:
            yield f"data: {json.dumps({'type': 'delta', 'content': chunk}, ensure_ascii=False, separators=(',', ':'))}\n\n"
        yield 'data: {"type":"done"}\n\n'
        yield "data: [DONE]\n\n"
    except LLMProviderError as exc:
        yield f"data: {json.dumps({'type': 'error', 'message': str(exc)}, ensure_ascii=False, separators=(',', ':'))}\n\n"
        yield "data: [DONE]\n\n"
    except Exception:
        yield 'data: {"type":"error","message":"模型服务暂时不可用"}\n\n'
        yield "data: [DONE]\n\n"
