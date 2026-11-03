from __future__ import annotations
from typing import Optional
from src.services.providers.base import BaseLLMProvider
from src.services.providers.mock_provider import MockLLMProvider
from src.services.providers.google_provider import GoogleGeminiProvider
from src.services.providers.openai_provider import OpenAIProvider
from src.services.providers.ollama_provider import OllamaProvider
from src.config import config

class ProviderFactory:
    """
    Фабрика создания LLM-провайдеров.
    Позволяет гибко переключаться между Ollama (Qwen), Google Gemini, OpenAI и Mock-режимом.
    """
    @staticmethod
    def get_provider(provider_type: Optional[str] = None) -> BaseLLMProvider:
        selected = (provider_type or config.DEFAULT_PROVIDER).lower()

        if selected in ("ollama", "qwen", "local"):
            return OllamaProvider()

        elif selected in ("google", "gemini"):
            if not config.GEMINI_API_KEY:
                return MockLLMProvider()
            return GoogleGeminiProvider()

        elif selected in ("openai", "gpt"):
            if not config.OPENAI_API_KEY:
                return MockLLMProvider()
            return OpenAIProvider()

        elif selected in ("mock", "offline"):
            return MockLLMProvider()

        else:
            return OllamaProvider()

__all__ = [
    "BaseLLMProvider",
    "MockLLMProvider",
    "GoogleGeminiProvider",
    "OpenAIProvider",
    "OllamaProvider",
    "ProviderFactory"
]
