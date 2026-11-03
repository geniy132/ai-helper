from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from src.config import config
from src.web.api.v1.router import api_v1_router

app = FastAPI(
    title=config.PROJECT_NAME,
    version=config.VERSION,
    description="AI-помощник для подготовки B2B-описаний товаров КИПиА",
    docs_url="/docs",
    redoc_url="/redoc",
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

if STATIC_DIR.exists():
    app.mount(
        "/static", StaticFiles(directory=str(STATIC_DIR)), name="static"
    )

# Подключение модульных маршрутов API (v1 и базовый префикс /api)
app.include_router(api_v1_router, prefix="/api")
app.include_router(api_v1_router, prefix="/api/v1")


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    """Отдаёт SVG-иконку для предотвращения ошибки 404 в браузере"""
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
        '<rect width="100" height="100" rx="20" fill="#2563eb"/>'
        '<rect x="25" y="25" width="50" height="50" rx="10" fill="#ffffff"/>'
        '<circle cx="50" cy="50" r="12" fill="#2563eb"/>'
        "</svg>"
    )
    return Response(content=svg, media_type="image/svg+xml")


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def serve_index():
    """Отдаёт основную страницу веб-интерфейса"""
    index_file = STATIC_DIR / "index.html"
    if not index_file.exists():
        return HTMLResponse(
            "<h1>UI static files not found</h1>", status_code=404
        )
    return FileResponse(index_file)
