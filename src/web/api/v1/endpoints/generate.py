from __future__ import annotations

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.models.product import ProductCardOutput, ProductInput
from src.services.generator import CardGenerationService
from src.web.dependencies import get_generator_service, verify_api_key

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Генерация"])


@router.post(
    "/generate",
    response_model=dict[str, Any],
    summary="Генерация карточки товара B2B",
    dependencies=[Depends(verify_api_key)],
)
async def generate_product_card(
    item: ProductInput,
    generator: Annotated[CardGenerationService, Depends(get_generator_service)],
    provider: str | None = Query(
        default=None, description="Провайдер LLM (ollama, mock)"
    ),
) -> dict[str, Any]:
    """
    Генерирует черновик карточки товара по входным данным прибора.
    Выполняет строгую Pydantic-валидацию входных данных, анти-галлюцинацию
    и возвращает результат в форматах JSON, Markdown и Plain Text.
    """
    try:
        card: ProductCardOutput = await generator.generate_from_dict(
            item.model_dump(), provider
        )

        response_payload = card.model_dump()
        response_payload["markdown"] = card.to_markdown()
        response_payload["plain_text"] = card.to_plain_text()
        return response_payload

    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Ошибка валидации входных данных: {ve}",
        ) from ve
    except Exception as e:
        logger.exception("Ошибка при генерации карточки")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Внутренняя ошибка генерации: {e}",
        ) from e
