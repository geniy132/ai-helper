from __future__ import annotations

from src.config import config
from src.services.providers.base import BaseLLMProvider
from src.services.providers.mock_provider import MockLLMProvider
from src.services.providers.ollama_provider import OllamaProvider


class ProviderFactory:
    """
    Фабрика создания LLM-провайдера.
    Основной выбранный провайдер: Ollama (Qwen).
    Резервный офлайн-провайдер: MockLLMProvider.
    """

    @staticmethod
    def get_provider(provider_type: str | None = None) -> BaseLLMProvider:
        selected = (provider_type or config.DEFAULT_PROVIDER).lower()

        if selected in ("mock", "offline"):
            return MockLLMProvider()

        # По умолчанию используется выбранная в проекте модель Ollama Qwen
        return OllamaProvider()


__all__ = [
    "BaseLLMProvider",
    "MockLLMProvider",
    "OllamaProvider",
    "ProviderFactory",
]
