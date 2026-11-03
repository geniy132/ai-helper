from __future__ import annotations

from fastapi import APIRouter

from src.web.api.v1.endpoints import generate, health, presets

api_v1_router = APIRouter()
api_v1_router.include_router(health.router)
api_v1_router.include_router(presets.router)
api_v1_router.include_router(generate.router)
