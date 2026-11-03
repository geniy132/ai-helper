from __future__ import annotations

from abc import ABC, abstractmethod

from src.models.product import ProductCardOutput, ProductInput


class BaseLLMProvider(ABC):
    """
    Абстрактный интерфейс провайдера языковой модели (LLM).
    """

    @abstractmethod
    async def generate_card(self, product: ProductInput) -> ProductCardOutput:
        """
        Генерирует черновик карточки товара на основе входных данных.
        """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Название используемого провайдера"""
