from __future__ import annotations

import re

from src.constants import (
    DATA_NOT_FOUND_LABEL,
    SEARCH_QUERIES_CLAMP,
    SEO_DESC_MAX_LEN,
    SEO_DESC_MIN_LEN,
    SEO_DESC_TRUNCATE_TARGET,
    SEO_TITLE_MAX_LEN,
)
from src.models.product import (
    CommercialBlock,
    ProductCardOutput,
    ProductInput,
)
from src.services.anti_hallucination import AntiHallucinationGuard
from src.services.providers.base import BaseLLMProvider
from src.texts import TEXTS


class MockLLMProvider(BaseLLMProvider):
    """
    Детерминированный офлайн-провайдер генерации.
    Позволяет тестировать систему без внешних сервисов,
    соблюдая строгие лимиты по символам (title <= 70, description 800-1200)
    и правила анти-галлюцинации.
    """

    @property
    def provider_name(self) -> str:
        return "Mock / Offline Deterministic Engine"

    async def generate_card(self, product: ProductInput) -> ProductCardOutput:
        texts = TEXTS["mock_provider"]
        vendor = product.manufacturer or ""
        base_name = product.name

        # 1. Формирование SEO-заголовка до 70 символов
        if vendor and vendor.lower() not in base_name.lower():
            full_title = f"{vendor} {base_name}"
        else:
            full_title = base_name

        suffix = texts["title_suffix"]
        if len(full_title) > SEO_TITLE_MAX_LEN:
            cutoff = SEO_TITLE_MAX_LEN - 3
            seo_title = full_title[:cutoff].rsplit(" ", 1)[0] + "..."
        elif len(full_title) + len(suffix) <= SEO_TITLE_MAX_LEN:
            seo_title = f"{full_title}{suffix}"
        else:
            seo_title = full_title

        # 2. Формирование характеристик исключительно из входных данных
        key_specs: dict[str, str] = {}
        for k, v in product.specs.items():
            key_specs[str(k)] = str(v)

        if not key_specs:
            key_specs["основные технические параметры"] = DATA_NOT_FOUND_LABEL

        # 3. Формирование поисковых запросов
        clean_name = re.sub(r"[^\w\s\-\.]", " ", product.name).strip()
        vendor_part = (
            f"{vendor} {clean_name} характеристики"
            if vendor
            else f"{clean_name} паспорт"
        )
        search_queries = [
            f"купить {clean_name}",
            f"{clean_name} цена с ндс",
            vendor_part,
            f"промышленный {clean_name} b2b",
        ]

        # 4. Формирование commercial-блока
        target_audience = texts["target_audience"]
        solved_problems = texts["solved_problems"]

        # 5. Формирование SEO-описания строго объемом 800-1200 символов
        if product.description:
            desc_intro = product.description.strip()
        else:
            vendor_label = vendor or "отечественных брендов"
            desc_intro = texts["desc_intro_fallback"].format(
                name=product.name, vendor=vendor_label
            )

        specs_summary = ", ".join(
            f"{k}: {v}" for k, v in list(key_specs.items())[:5]
        )

        body_p1 = texts["body_p1_template"].format(
            name=product.name, specs_summary=specs_summary
        )
        body_p2 = texts["body_p2"]

        full_desc = f"{desc_intro} {body_p1} {body_p2}".strip()
        full_desc = " ".join(full_desc.split())

        # Точная подгонка длины под 800 - 1200 символов
        if len(full_desc) < SEO_DESC_MIN_LEN:
            full_desc += texts["filler"]
        elif len(full_desc) > SEO_DESC_MAX_LEN:
            full_desc = (
                full_desc[:SEO_DESC_TRUNCATE_TARGET].rsplit(".", 1)[0] + "."
            )

        card = ProductCardOutput(
            seo_title=seo_title,
            seo_description=full_desc,
            key_specs=key_specs,
            search_queries=search_queries[:SEARCH_QUERIES_CLAMP],
            commercial_block=CommercialBlock(
                target_audience=target_audience,
                solved_problems=solved_problems,
            ),
            missing_fields=[],
        )

        # Пропускаем через верификатор анти-галлюцинаций
        card = AntiHallucinationGuard.verify_and_sanitize(card, product)
        return card
