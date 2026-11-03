from __future__ import annotations
import json
import logging
import re
from typing import Optional
from openai import AsyncOpenAI

from src.models.product import ProductInput, ProductCardOutput
from src.services.providers.base import BaseLLMProvider
from src.services.anti_hallucination import AntiHallucinationGuard
from src.prompts.templates import SYSTEM_PROMPT, format_user_prompt
from src.config import config

logger = logging.getLogger(__name__)

class OpenAIProvider(BaseLLMProvider):
    """
    Провайдер интеграции с OpenAI API (и совместимыми сервисами: Ollama, Groq, vLLM).
    Использует response_format json_object.
    """

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or config.OPENAI_API_KEY
        self.model_name = model_name or config.OPENAI_MODEL
        self.base_url = base_url or config.OPENAI_BASE_URL
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY не установлен. Проверьте .env или укажите ключ.")
        self.client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)

    @property
    def provider_name(self) -> str:
        return f"OpenAI ({self.model_name})"

    async def generate_card(self, product: ProductInput) -> ProductCardOutput:
        user_prompt = format_user_prompt(product.model_dump())

        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.2
            )

            raw_text = response.choices[0].message.content or "{}"
            cleaned_json_str = re.sub(r"^```json\s*", "", raw_text.strip())
            cleaned_json_str = re.sub(r"```$", "", cleaned_json_str.strip())
            data = json.loads(cleaned_json_str)

            card = ProductCardOutput(**data)
            sanitized_card = AntiHallucinationGuard.verify_and_sanitize(card, product)
            return sanitized_card

        except Exception as e:
            logger.error(f"Ошибка вызова OpenAI API: {e}")
            raise RuntimeError(f"Сбой при обращении к OpenAI API: {str(e)}") from e
