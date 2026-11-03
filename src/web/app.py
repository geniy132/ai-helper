from __future__ import annotations
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any

from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from src.models.product import ProductInput, ProductCardOutput
from src.services.generator import default_generator_service
from src.config import config

logger = logging.getLogger(__name__)

app = FastAPI(
    title=config.PROJECT_NAME,
    version=config.VERSION,
    description="AI-помощник для подготовки B2B-описаний товаров КИПиА"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = Path(__file__).resolve().parent / "static"
DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/api/health")
async def health_check():
    """Проверка состояния сервиса и доступных провайдеров"""
    return {
        "status": "healthy",
        "version": config.VERSION,
        "selected_model": config.OLLAMA_MODEL,
        "default_provider": config.DEFAULT_PROVIDER,
        "providers_available": {
            "ollama_qwen": True,
            "mock_fallback": True
        }
    }


@app.get("/api/presets")
async def get_presets():
    """Возвращает предустановленные примеры товаров (включая Союз-Прибор)"""
    samples_path = DATA_DIR / "samples.json"
    if not samples_path.exists():
        return []
    with open(samples_path, "r", encoding="utf-8") as f:
        return json.load(f)


@app.post("/api/generate")
async def generate_product_card(
    item: Dict[str, Any],
    provider: Optional[str] = Query(default=None, description="Провайдер LLM (mock, google, openai)")
):
    """
    Генерирует черновик карточки товара по входным данным JSON.
    Возвращает структурированный результат вместе с отрендеренным Markdown и Plain Text.
    """
    try:
        # Проверяем и генерируем
        card: ProductCardOutput = await default_generator_service.generate_from_dict(item, provider)
        
        response_payload = card.model_dump()
        response_payload["markdown"] = card.to_markdown()
        response_payload["plain_text"] = card.to_plain_text()
        
        return response_payload
        
    except ValueError as ve:
        raise HTTPException(status_code=422, detail=f"Ошибка валидации входных данных: {str(ve)}")
    except Exception as e:
        logger.exception("Ошибка при генерации карточки")
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка генерации: {str(e)}")


@app.get("/", response_class=HTMLResponse)
async def serve_index():
    """Отдаёт основную страницу веб-интерфейса"""
    index_file = STATIC_DIR / "index.html"
    if not index_file.exists():
        return HTMLResponse("<h1>UI static files not found</h1>", status_code=404)
    with open(index_file, "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())
