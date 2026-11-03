from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from src.config import config

router = APIRouter(tags=["Мониторинг"])


@router.get("/health", summary="Проверка состояния сервиса")
async def health_check() -> dict[str, Any]:
    """Возвращает статус доступности сервиса и активной модели."""
    return {
        "status": "healthy",
        "version": config.VERSION,
        "selected_model": config.OLLAMA_MODEL,
        "default_provider": config.DEFAULT_PROVIDER,
        "providers_available": {
            "ollama_qwen": True,
            "mock_fallback": True,
        },
    }
