from app.services.llm.clients.openai_client import OpenAIClient


class QwenClient(OpenAIClient):
    model_id = "qwen"
    provider_name = "qwen"
