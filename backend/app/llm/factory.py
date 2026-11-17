from app.core.config import settings
from app.core.limits import (
    LLM_MAX_CALLS_PER_ANALYSIS,
    LLM_MAX_INPUT_CHARS,
    LLM_MAX_RETRIES,
)
from app.llm.client import LLMClient
from app.llm.demo import DemoLLMClient


def create_llm_client() -> LLMClient:
    provider = settings.llm_provider.strip().lower()

    if provider == "demo":
        return DemoLLMClient()

    return LLMClient(
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        model=settings.llm_model,
        timeout_seconds=(settings.llm_timeout_seconds),
        max_retries=LLM_MAX_RETRIES,
        max_calls=LLM_MAX_CALLS_PER_ANALYSIS,
        max_input_chars=LLM_MAX_INPUT_CHARS,
    )
