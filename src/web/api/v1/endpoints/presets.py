from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter

from src.config import DATA_DIR

router = APIRouter(tags=["Каталог"])


@router.get("/presets", summary="Предустановленные примеры товаров")
def get_presets() -> list[dict[str, Any]]:
    """Возвращает примеры товаров из каталога Союз-Прибор."""
    samples_path = DATA_DIR / "samples.json"
    if not samples_path.exists():
        return []
    with open(samples_path, encoding="utf-8") as f:
        return json.load(f)
