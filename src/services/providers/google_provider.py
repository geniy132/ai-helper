from __future__ import annotations
import json
import logging
import re
from typing import Optional
from google import genai
from google.genai import types

from src.models.product import ProductInput, ProductCardOutput
from src.services.providers.base import BaseLLMProvider
from src.services.anti_hallucination import AntiHallucinationGuard
from src.prompts.templates import SYSTEM_PROMPT, format_user_prompt
from src.config import config

logger = logging.getLogger(__name__)

class GoogleGeminiProvider(BaseLLMProvider):
    """
    Провайдер интеграции с Google Gemini API.
    Использует структурированный JSON Schema режим генерации.
    """

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key or config.GEMINI_API_KEY
        self.model_name = model_name or config.GEMINI_MODEL
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY не установлен. Проверьте .env или укажите ключ.")
        self.client = genai.Client(api_key=self.api_key)

    @property
    def provider_name(self) -> str:
        return f"Google Gemini ({self.model_name})"

    async def generate_card(self, product: ProductInput) -> ProductCardOutput:
        user_prompt = format_user_prompt(product.model_dump())

        try:
            # Вызов Gemini API
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    response_mime_type="application/json",
                    temperature=0.2,
                )
            )

            raw_text = response.text or "{}"
            # Очищаем от возможных артефактов markdown
            cleaned_json_str = re.sub(r"^```json\s*", "", raw_text.strip())
            cleaned_json_str = re.sub(r"```$", "", cleaned_json_str.strip())
            data = json.loads(cleaned_json_str)

            card = ProductCardOutput(**data)
            # Пропускаем через защитный контур анти-галлюцинаций
            sanitized_card = AntiHallucinationGuard.verify_and_sanitize(card, product)
            return sanitized_card

        except Exception as e:
            logger.error(f"Ошибка вызова Google Gemini API: {e}")
            raise RuntimeError(f"Сбой при обращении к Gemini API: {str(e)}") from e
