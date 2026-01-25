# src/llm/factory.py
from src.llm.config import LLMSettings
from src.llm.base_client import BaseLLMClient
from src.llm.mock_client import MockLLMClient
from src.llm.real.gemini_client import GeminiClient


def create_llm_client(settings: LLMSettings | None = None) -> BaseLLMClient:
    """
    Factory central de clientes LLM para K9.
    """

    settings = settings or LLMSettings()

    if settings.provider == "mock":
        return MockLLMClient()

    if settings.provider == "gemini":
        return GeminiClient(
            api_key=settings.gemini_api_key,
            model=settings.gemini_model,
        )

    raise ValueError(f"Proveedor LLM no soportado: {settings.provider}")
