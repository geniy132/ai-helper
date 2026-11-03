from __future__ import annotations

import re

from src.models.product import CommercialBlock, ProductCardOutput, ProductInput
from src.services.anti_hallucination import AntiHallucinationGuard
from src.services.providers.base import BaseLLMProvider


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
        # 1. Формирование SEO-заголовка до 70 символов
        vendor = product.manufacturer or ""
        base_name = product.name
        if vendor and vendor.lower() not in base_name.lower():
            full_title = f"{vendor} {base_name}"
        else:
            full_title = base_name

        # Ограничиваем до 70 символов
        if len(full_title) > 70:
            seo_title = full_title[:67].rsplit(" ", 1)[0] + "..."
        else:
            # Если есть место, добавляем полезный суффикс КИПиА
            suffix = " — купить в B2B"
            if len(full_title) + len(suffix) <= 70:
                seo_title = f"{full_title}{suffix}"
            else:
                seo_title = full_title

        # 2. Формирование характеристик исключительно из входных данных
        key_specs: dict[str, str] = {}
        for k, v in product.specs.items():
            key_specs[str(k)] = str(v)

        if not key_specs:
            key_specs["основные технические параметры"] = "данных нет"

        # 3. Формирование поисковых запросов
        clean_name = re.sub(r"[^\w\s\-\.]", " ", product.name).strip()
        search_queries = [
            f"купить {clean_name}",
            f"{clean_name} цена с ндс",
            f"{vendor} {clean_name} характеристики"
            if vendor
            else f"{clean_name} паспорт",
            f"промышленный {clean_name} b2b",
        ]

        # 4. Формирование commercial-блока
        target_audience = (
            "Инженеры КИПиА, системные интеграторы АСУ ТП, "
            "проектировщики систем автоматизации и отделы МТО "
            "промышленных предприятий."
        )
        solved_problems = (
            "Прибор решает задачи надежного контроля, автоматизации и "
            "сбора технологических параметров на производственных линиях, "
            "объектах энергетики и инженерной инфраструктуры."
        )

        # 5. Формирование SEO-описания строго объемом 800-1200 символов
        if product.description:
            desc_intro = product.description.strip()
        else:
            vendor_label = vendor or "отечественных брендов"
            desc_intro = (
                f"Промышленное оборудование {product.name} от производителя "
                f"{vendor_label} предназначено для применения в "
                "автоматизированных системах управления "
                "технологическими процессами."
            )

        specs_summary = ", ".join(
            f"{k}: {v}" for k, v in list(key_specs.items())[:5]
        )

        body_p1 = (
            f"{product.name} представляет собой надежное техническое "
            "решение для задач промышленного контроля и диспетчеризации. "
            "Оборудование обеспечивает стабильную эксплуатацию в "
            "регламентированных диапазонах, соответствует отраслевым "
            "стандартам и спроектировано для цеховых условий среды. "
            f"Среди ключевых параметров: {specs_summary}. "
        )

        body_p2 = (
            "Устройство оптимизировано для интеграции в действующие "
            "комплексы АСУ ТП, шкафы автоматики и распределенные сети. "
            "Применение качественной элементной базы гарантирует высокую "
            "помехоустойчивость и минимальные эксплуатационные затраты. "
            "Поставка прибора осуществляется с полным комплектом "
            "технической документации, паспортом и гарантией для "
            "корпоративных заказчиков и оптовых поставок."
        )

        full_desc = f"{desc_intro} {body_p1} {body_p2}".strip()
        full_desc = " ".join(full_desc.split())

        # Точная подгонка длины под 800 - 1200 символов
        if len(full_desc) < 800:
            filler = (
                " Продукция доступна со склада с возможностью оперативной "
                "отгрузки по всей России. Оборудование сертифицировано и "
                "готово к промышленному вводу в эксплуатацию."
            )
            full_desc += filler
        elif len(full_desc) > 1200:
            full_desc = full_desc[:1180].rsplit(".", 1)[0] + "."

        card = ProductCardOutput(
            seo_title=seo_title,
            seo_description=full_desc,
            key_specs=key_specs,
            search_queries=search_queries[:5],
            commercial_block=CommercialBlock(
                target_audience=target_audience,
                solved_problems=solved_problems,
            ),
            missing_fields=[],
        )

        # Пропускаем через верификатор анти-галлюцинаций
        card = AntiHallucinationGuard.verify_and_sanitize(card, product)
        return card
