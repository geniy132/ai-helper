from __future__ import annotations

import json
import logging
from typing import Any

from src.models.product import ProductCardOutput, ProductInput
from src.services.providers import BaseLLMProvider, ProviderFactory

logger = logging.getLogger(__name__)


class CardGenerationService:
    """
    Основной оркестратор сервиса генерации карточек товаров.
    """

    def __init__(self, provider: BaseLLMProvider | None = None):
        self._provider = provider

    def _get_provider(
        self, provider_type: str | None = None
    ) -> BaseLLMProvider:
        if self._provider:
            return self._provider
        return ProviderFactory.get_provider(provider_type)

    async def generate_from_dict(
        self, data: dict[str, Any], provider_type: str | None = None
    ) -> ProductCardOutput:
        """
        Генерирует карточку по словарю
        с автоматической валидацией через Pydantic.
        """
        product_input = ProductInput(**data)
        provider = self._get_provider(provider_type)
        logger.info(
            f"Запуск генерации для '{product_input.name}' "
            f"через провайдер: {provider.provider_name}"
        )

        card = await provider.generate_card(product_input)
        return card

    async def generate_from_json_string(
        self, json_str: str, provider_type: str | None = None
    ) -> ProductCardOutput:
        """
        Парсит JSON-строку и выполняет генерацию.
        """
        try:
            data = json.loads(json_str)
        except Exception as e:
            raise ValueError(
                f"Некорректный синтаксис входного JSON: {e}"
            ) from e

        return await self.generate_from_dict(data, provider_type)


default_generator_service = CardGenerationService()
