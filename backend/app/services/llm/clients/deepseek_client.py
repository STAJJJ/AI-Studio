from app.services.llm.clients.openai_client import OpenAIClient


class DeepSeekClient(OpenAIClient):
    model_id = "deepseek"
    provider_name = "deepseek"
