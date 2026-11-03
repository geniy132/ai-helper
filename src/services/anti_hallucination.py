from __future__ import annotations

import re

from src.constants import (
    DATA_NOT_FOUND_LABEL,
    DATA_UNVERIFIED_SUFFIX,
    MIN_DESCRIPTION_LEN_FOR_AUDIT,
    SEO_DESC_MAX_LEN,
    SEO_DESC_MIN_LEN,
    SEO_DESC_TRUNCATE_TARGET,
    SEO_TITLE_MAX_LEN,
)
from src.models.product import (
    MissingFieldInfo,
    ProductCardOutput,
    ProductInput,
)
from src.texts import TEXTS


class AntiHallucinationGuard:
    """
    Верификатор достоверности технических характеристик и полноты данных.
    Предотвращает выдумывание технических параметров языковыми моделями.
    """

    @classmethod
    def get_critical_fields(cls) -> list[tuple[str, tuple[str, ...]]]:
        """Загружает список критических ТТХ и ключевых слов из texts.json."""
        raw_fields = TEXTS["audit"].get("critical_fields", [])
        return [
            (item["field_name"], tuple(item["keywords"]))
            for item in raw_fields
        ]

    @classmethod
    def audit_input_completeness(
        cls, item: ProductInput
    ) -> list[MissingFieldInfo]:
        """
        Аудит входных данных на предмет пропущенных
        или требующих уточнения полей.
        """
        warnings: list[MissingFieldInfo] = []
        messages = TEXTS["audit"]["messages"]

        # 1. Проверка производителя
        if not item.manufacturer or not item.manufacturer.strip():
            warnings.append(
                MissingFieldInfo(
                    field_name="Производитель",
                    message=messages["missing_manufacturer"],
                    severity="warning",
                )
            )

        # 2. Проверка описания
        if (
            not item.description
            or len(item.description.strip()) < MIN_DESCRIPTION_LEN_FOR_AUDIT
        ):
            warnings.append(
                MissingFieldInfo(
                    field_name="Текстовое описание / паспорт",
                    message=messages["missing_description"],
                    severity="info",
                )
            )

        # 3. Проверка критических ТТХ
        specs_keys_lower = " ".join([str(k).lower() for k in item.specs])
        specs_vals_lower = " ".join(
            [str(v).lower() for v in item.specs.values()]
        )
        all_text = (
            f"{item.name.lower()} {specs_keys_lower} {specs_vals_lower} "
            f"{(item.description or '').lower()}"
        )

        for field_name, keywords in cls.get_critical_fields():
            has_param = any(kw in all_text for kw in keywords)
            if not has_param:
                msg = messages["missing_param_template"].format(
                    field_name=field_name
                )
                warnings.append(
                    MissingFieldInfo(
                        field_name=field_name.capitalize(),
                        message=msg,
                        severity="warning",
                    )
                )

        return warnings

    @classmethod
    def verify_and_sanitize(
        cls, card: ProductCardOutput, input_data: ProductInput
    ) -> ProductCardOutput:
        """
        Верифицирует сгенерированную карточку:
        - Проверяет отсутствие галлюцинаций в ТТХ;
        - Дополняет предупреждениями об отсутствующих полях;
        - Корректирует длину SEO-заголовка и SEO-описания по лимитам ТЗ.
        """
        raw_source_text = (
            f"{input_data.name} {input_data.manufacturer} "
            f"{input_data.description} "
            + " ".join(f"{k} {v}" for k, v in input_data.specs.items())
        )
        raw_source_normalized = raw_source_text.lower()
        missing_markers = TEXTS["audit"]["missing_markers"]

        sanitized_specs: dict[str, str] = {}
        for k, v in card.key_specs.items():
            val_str = str(v).strip()
            # Если значение помечено как отсутствующее
            if any(term in val_str.lower() for term in missing_markers):
                sanitized_specs[k] = DATA_NOT_FOUND_LABEL
                continue

            # Извлекаем числовые метрики из значения
            # (например, '0-1.6', '63х110')
            numbers = re.findall(r"\b\d+(?:[.,]\d+)?\b", val_str)
            hallucinated = False
            for num in numbers:
                num_alt = (
                    num.replace(",", ".")
                    if "," in num
                    else num.replace(".", ",")
                )
                if (
                    num not in raw_source_normalized
                    and num_alt not in raw_source_normalized
                    and (len(num) > 1 or num not in raw_source_normalized)
                ):
                    hallucinated = True
                    break

            if hallucinated:
                sanitized_specs[k] = f"{val_str} ({DATA_UNVERIFIED_SUFFIX})"
                card.is_hallucination_free = False
            else:
                sanitized_specs[k] = val_str

        card.key_specs = sanitized_specs

        # Дополняем аудитными замечаниями
        input_warnings = cls.audit_input_completeness(input_data)
        existing_fields = {m.field_name for m in card.missing_fields}
        for w in input_warnings:
            if w.field_name not in existing_fields:
                card.missing_fields.append(w)

        # Контроль длины SEO-заголовка (жесткий лимит до 70 символов)
        if len(card.seo_title) > SEO_TITLE_MAX_LEN:
            cutoff = SEO_TITLE_MAX_LEN - 3
            trimmed = card.seo_title[:cutoff].rsplit(" ", 1)[0] + "..."
            card.seo_title = trimmed

        # Контроль объема SEO-описания (диапазон 800-1200 символов)
        current_desc = " ".join(card.seo_description.split())
        enrichment = TEXTS["audit"]["enrichment_text"]
        if len(current_desc) < SEO_DESC_MIN_LEN:
            while len(current_desc) < SEO_DESC_MIN_LEN:
                current_desc += enrichment
                current_desc = " ".join(current_desc.split())
            if len(current_desc) > SEO_DESC_MAX_LEN:
                current_desc = (
                    current_desc[:SEO_DESC_TRUNCATE_TARGET].rsplit(".", 1)[0]
                    + "."
                )

        elif len(current_desc) > SEO_DESC_MAX_LEN:
            current_desc = (
                current_desc[:SEO_DESC_TRUNCATE_TARGET].rsplit(".", 1)[0] + "."
            )

        card.seo_description = current_desc
        card.seo_title_length = len(card.seo_title)
        card.seo_description_length = len(card.seo_description)

        return card
