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

class OllamaProvider(BaseLLMProvider):
    """
    Провайдер интеграции с локальной Ollama (Qwen 2.5 Coder).
    Работает через локальный порт 11434 по OpenAI-совместимому протоколу.
    100% бесплатно, безопасно и локально на GPU.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        model_name: Optional[str] = None
    ):
        self.base_url = base_url or config.OLLAMA_BASE_URL
        self.model_name = model_name or config.OLLAMA_MODEL
        self.client = AsyncOpenAI(
            base_url=self.base_url,
            api_key="ollama"  # Ollama не требует реального ключа
        )

    @property
    def provider_name(self) -> str:
        return f"Ollama Local ({self.model_name})"

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
            # Пропускаем через программный защитный слой от галлюцинаций
            sanitized_card = AntiHallucinationGuard.verify_and_sanitize(card, product)
            return sanitized_card

        except Exception as e:
            logger.error(f"Ошибка вызова Ollama ({self.model_name}): {e}")
            raise RuntimeError(f"Сбой при обращении к локальной Ollama: {str(e)}") from e
