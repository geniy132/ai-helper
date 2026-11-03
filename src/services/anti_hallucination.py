from __future__ import annotations
import re
from typing import Dict, Any, List, Tuple
from src.models.product import ProductInput, ProductCardOutput, MissingFieldInfo

class AntiHallucinationGuard:
    """
    Верификатор достоверности технических характеристик и полноты данных.
    Предотвращает выдумывание технических параметров языковыми моделями.
    """

    CRITICAL_EQUIPMENT_FIELDS = [
        ("напряжение питания", ["питание", "напряжение", "power", "в", "vac", "vdc"]),
        ("интерфейс связи", ["интерфейс", "rs-485", "rs-232", "ethernet", "can", "usb"]),
        ("степень защиты", ["степень защиты", "ip", "защита"]),
        ("диапазон измерений / входы", ["диапазон", "вход", "выход", "канал"]),
    ]

    @classmethod
    def audit_input_completeness(cls, item: ProductInput) -> List[MissingFieldInfo]:
        """
        Аудит входных данных на предмет пропущенных или требующих уточнения полей.
        """
        warnings: List[MissingFieldInfo] = []

        # 1. Проверка производителя
        if not item.manufacturer or not item.manufacturer.strip():
            warnings.append(MissingFieldInfo(
                field_name="Производитель",
                message="Не указан производитель (бренд) прибора. Требуется уточнить для корректного SEO и гарантии.",
                severity="warning"
            ))

        # 2. Проверка описания
        if not item.description or len(item.description.strip()) < 30:
            warnings.append(MissingFieldInfo(
                field_name="Текстовое описание / паспорт",
                message="Отсутствует подробное техническое описание или фрагмент паспорта. Карточка сформирована на основе кратких ТТХ.",
                severity="info"
            ))

        # 3. Проверка критических ТТХ
        specs_keys_lower = " ".join([str(k).lower() for k in item.specs.keys()])
        specs_vals_lower = " ".join([str(v).lower() for v in item.specs.values()])
        all_text = f"{item.name.lower()} {specs_keys_lower} {specs_vals_lower} {(item.description or '').lower()}"

        for field_name, keywords in cls.CRITICAL_EQUIPMENT_FIELDS:
            has_param = any(kw in all_text for kw in keywords)
            if not has_param:
                warnings.append(MissingFieldInfo(
                    field_name=field_name.capitalize(),
                    message=f"Параметр «{field_name}» не найден во входных данных. В карточке указано «данных нет».",
                    severity="warning"
                ))

        return warnings

    @classmethod
    def verify_and_sanitize(cls, card: ProductCardOutput, input_data: ProductInput) -> ProductCardOutput:
        """
        Верифицирует сгенерированную карточку:
        - Проверяет отсутствие галлюцинаций в ТТХ;
        - Дополняет предупреждениями об отсутствующих полях;
        - Корректирует длину SEO-заголовка, если модель превысила 70 символов.
        """
        raw_source_text = f"{input_data.name} {input_data.manufacturer} {input_data.description} " + \
                          " ".join(f"{k} {v}" for k, v in input_data.specs.items())
        raw_source_normalized = raw_source_text.lower()

        sanitized_specs: Dict[str, str] = {}
        for k, v in card.key_specs.items():
            val_str = str(v).strip()
            # Если значение помечено как отсутствующее
            if any(term in val_str.lower() for term in ["данных нет", "не указан", "нет данных", "н/д", "n/a"]):
                sanitized_specs[k] = "данных нет"
                continue

            # Извлекаем числовые метрики из значения (например, '0-1.6', '115200', '63х110')
            numbers = re.findall(r"\b\d+(?:[.,]\d+)?\b", val_str)
            hallucinated = False
            for num in numbers:
                # Нормализуем запятую и точку
                num_alt = num.replace(",", ".") if "," in num else num.replace(".", ",")
                if num not in raw_source_normalized and num_alt not in raw_source_normalized:
                    # Если число отсутствует в источнике, проверяем, не является ли это выдумкой
                    # Исключаем тривиальные счетчики (типа 1, 2 для портов, если упомянуты)
                    if len(num) > 1 or num not in raw_source_normalized:
                        hallucinated = True
                        break

            if hallucinated:
                # Заменяем вымышленное значение на безопасную пометку
                sanitized_specs[k] = f"{val_str} (требует уточнения: нет в паспорте)"
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
        if len(card.seo_title) > 70:
            trimmed = card.seo_title[:67].rsplit(" ", 1)[0] + "..."
            card.seo_title = trimmed

        card.seo_title_length = len(card.seo_title)
        card.seo_description_length = len(card.seo_description)

        return card
