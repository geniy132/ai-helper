from __future__ import annotations
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

class Config:
    PROJECT_NAME: str = "B2B AI Product Card Assistant"
    VERSION: str = "0.1"
    
    # Выбранный по ТЗ LLM-провайдер: "ollama" (или "mock" для оффлайн-проверки)
    DEFAULT_PROVIDER: str = os.getenv("LLM_PROVIDER", "ollama").lower()
    
    # Настройки локальной модели Ollama
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:1.5b")
    
    # Настройки сервера
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")

config = Config()
