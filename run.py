#!/usr/bin/env python3
"""
Удобный скрипт для запуска веб-сервера проекта.
Использование: python run.py
"""

import uvicorn

from src.config import config

if __name__ == "__main__":
    print(f"==> Запуск {config.PROJECT_NAME}")
    print(f"==> Адрес: http://{config.HOST}:{config.PORT}")
    print(f"==> Выбранная модель: {config.OLLAMA_MODEL} (Ollama)")
    uvicorn.run(
        "src.web.app:app",
        host=config.HOST,
        port=config.PORT,
        reload=config.DEBUG,
    )
