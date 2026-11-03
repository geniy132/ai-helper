from __future__ import annotations

import json
from pathlib import Path
from typing import Any

TEXTS_FILE = Path(__file__).resolve().parent.parent / "data" / "texts.json"


def _load_texts() -> dict[str, Any]:
    if not TEXTS_FILE.exists():
        raise FileNotFoundError(
            f"Файл локализации и текстов не найден: {TEXTS_FILE}"
        )
    with open(TEXTS_FILE, encoding="utf-8") as f:
        return json.load(f)


TEXTS: dict[str, Any] = _load_texts()
