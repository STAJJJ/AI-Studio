from fastapi import APIRouter, HTTPException, status

from app.schemas.chat import ChatCompletionRequest, ChatCompletionResponse, ModelListResponse
from app.services.llm.gateway import llm_gateway
from app.services.llm.registry import LLMClientNotFoundError

router = APIRouter(tags=["LLM"])


@router.get("/models", response_model=ModelListResponse)
def list_models() -> ModelListResponse:
    return llm_gateway.list_models()


@router.post("/chat/completions", response_model=ChatCompletionResponse)
def create_chat_completion(request: ChatCompletionRequest) -> ChatCompletionResponse:
    try:
        return llm_gateway.chat(request)
    except LLMClientNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
