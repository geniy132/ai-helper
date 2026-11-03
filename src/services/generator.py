from __future__ import annotations
import json
import logging
from typing import Dict, Any, Optional
from src.models.product import ProductInput, ProductCardOutput
from src.services.providers import ProviderFactory, BaseLLMProvider

logger = logging.getLogger(__name__)

class CardGenerationService:
    """
    Основной оркестратор сервиса генерации карточек товаров.
    """

    def __init__(self, provider: Optional[BaseLLMProvider] = None):
        self._provider = provider

    def _get_provider(self, provider_type: Optional[str] = None) -> BaseLLMProvider:
        if self._provider:
            return self._provider
        return ProviderFactory.get_provider(provider_type)

    async def generate_from_dict(self, data: Dict[str, Any], provider_type: Optional[str] = None) -> ProductCardOutput:
        """
        Генерирует карточку по словарю с автоматической валидацией через Pydantic.
        """
        product_input = ProductInput(**data)
        provider = self._get_provider(provider_type)
        logger.info(f"Запуск генерации для '{product_input.name}' через провайдер: {provider.provider_name}")
        
        card = await provider.generate_card(product_input)
        return card

    async def generate_from_json_string(self, json_str: str, provider_type: Optional[str] = None) -> ProductCardOutput:
        """
        Парсит JSON-строку и выполняет генерацию.
        """
        try:
            data = json.loads(json_str)
        except Exception as e:
            raise ValueError(f"Некорректный синтаксис входного JSON: {e}") from e

        return await self.generate_from_dict(data, provider_type)

default_generator_service = CardGenerationService()
