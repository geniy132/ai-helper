from __future__ import annotations

import os
from typing import Annotated

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from src.services.generator import (
    CardGenerationService,
    default_generator_service,
)

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


def get_generator_service() -> CardGenerationService:
    """Внедрение зависимости сервиса генерации карточек."""
    return default_generator_service


def verify_api_key(
    api_key: Annotated[str | None, Security(API_KEY_HEADER)] = None,
) -> bool:
    """
    Проверка прав доступа (Permission check).
    Если задана переменная API_KEY в .env, требует заголовок X-API-Key.
    Если API_KEY не задан, разрешает свободный локальный доступ (MVP режим).
    """
    required_key = os.getenv("API_KEY", "").strip()
    if not required_key:
        return True

    if not api_key or api_key != required_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав: неверный или отсутствующий API-ключ",
        )
    return True
