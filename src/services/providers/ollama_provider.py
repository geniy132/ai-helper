from __future__ import annotations

import json
import logging
import re

import httpx

from src.config import config
from src.constants import DEFAULT_TEMPERATURE, DEFAULT_TIMEOUT_SEC
from src.models.product import ProductCardOutput, ProductInput
from src.prompts.templates import SYSTEM_PROMPT, format_user_prompt
from src.services.anti_hallucination import AntiHallucinationGuard
from src.services.providers.base import BaseLLMProvider

logger = logging.getLogger(__name__)


class OllamaProvider(BaseLLMProvider):
    """
    Провайдер интеграции с выбранной моделью Ollama Qwen.
    Использует нативный REST API Ollama (/api/chat)
    через легковесный асинхронный httpx.
    """

    def __init__(
        self,
        base_url: str | None = None,
        model_name: str | None = None,
        timeout: float = DEFAULT_TIMEOUT_SEC,
    ):
        self.base_url = (base_url or config.OLLAMA_BASE_URL).rstrip("/")
        self.model_name = model_name or config.OLLAMA_MODEL
        self.timeout = timeout

    @property
    def provider_name(self) -> str:
        return f"Ollama ({self.model_name})"

    async def generate_card(self, product: ProductInput) -> ProductCardOutput:
        user_prompt = format_user_prompt(product.model_dump())

        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "format": "json",
            "stream": False,
            "options": {"temperature": DEFAULT_TEMPERATURE},
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()

            res_json = response.json()
            raw_text = res_json.get("message", {}).get("content", "{}")

            cleaned_json_str = re.sub(r"^```json\s*", "", raw_text.strip())
            cleaned_json_str = re.sub(r"```$", "", cleaned_json_str.strip())

            try:
                data = json.loads(cleaned_json_str)
            except json.JSONDecodeError as jde:
                # Резервная попытка извлечь корневой JSON-объект
                match = re.search(r"\{[\s\S]*\}", cleaned_json_str)
                if match:
                    data = json.loads(match.group(0))
                else:
                    raise ValueError(
                        f"Модель {self.model_name} вернула невалидный JSON: "
                        f"{cleaned_json_str[:120]}"
                    ) from jde

            card = ProductCardOutput(**data)
            sanitized_card = AntiHallucinationGuard.verify_and_sanitize(
                card, product
            )
            return sanitized_card

        except httpx.ConnectError as ce:
            logger.error(
                f"Не удалось подключиться к Ollama на {self.base_url}: {ce}"
            )
            raise RuntimeError(
                f"Локальный сервер Ollama не отвечает на {self.base_url}. "
                "Убедитесь, что сервис запущен: 'ollama serve'"
            ) from ce
        except httpx.HTTPStatusError as hse:
            if hse.response.status_code == 404:
                raise RuntimeError(
                    f"Модель '{self.model_name}' не найдена в Ollama. "
                    f"Скачайте её командой: 'ollama pull {self.model_name}'"
                ) from hse
            raise RuntimeError(
                f"Ошибка сервера Ollama (HTTP {hse.response.status_code}): "
                f"{hse.response.text[:100]}"
            ) from hse
        except httpx.TimeoutException as te:
            raise RuntimeError(
                f"Превышено время ожидания ответа от Ollama ({self.timeout}с). "
                "Повторите попытку или выберите более лёгкую модель."
            ) from te
        except Exception as e:
            logger.error(
                f"Ошибка генерации через Ollama ({self.model_name}): {e}"
            )
            raise RuntimeError(
                f"Сбой генерации карточки через Ollama: {e}"
            ) from e
