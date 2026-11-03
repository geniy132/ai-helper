from src.models.product import (
    CommercialBlock,
    ProductCardOutput,
    ProductInput,
)
from src.services.anti_hallucination import AntiHallucinationGuard


def test_missing_field_detection():
    # Товар без производителя и без интерфейса
    item = ProductInput(
        name="Термометр ТТЖ",
        manufacturer="",
        specs={"диапазон": "0-100 C"},
        description="Технический термометр",
    )
    warnings = AntiHallucinationGuard.audit_input_completeness(item)
    warning_fields = [w.field_name for w in warnings]

    assert "Производитель" in warning_fields
    assert "Интерфейс связи" in warning_fields


def test_anti_hallucination_sanitizes_unbacked_data():
    item = ProductInput(
        name="Датчик давления",
        manufacturer="ПромПрибор",
        specs={"выходной сигнал": "4-20 мА"},
        description="Датчик для измерения",
    )
    # Предположим, модель выдумала диапазон '9999 Бар',
    # которого нет в источнике
    raw_card = ProductCardOutput(
        seo_title="Датчик давления ПромПрибор 4-20 мА",
        seo_description="Датчик давления промышленного типа."
        + (" подробное описание" * 40),
        key_specs={
            "выходной сигнал": "4-20 мА",
            "диапазон измерений": "9999 Бар",  # Галлюцинация
        },
        search_queries=["запрос 1", "запрос 2", "запрос 3"],
        commercial_block=CommercialBlock(
            target_audience="Инженеры", solved_problems="Контроль"
        ),
    )

    sanitized = AntiHallucinationGuard.verify_and_sanitize(raw_card, item)
    assert not sanitized.is_hallucination_free
    assert (
        "требует уточнения: нет в паспорте"
        in sanitized.key_specs["диапазон измерений"]
    )
    assert sanitized.key_specs["выходной сигнал"] == "4-20 мА"


def test_seo_title_truncation():
    item = ProductInput(name="Прибор", specs={})
    long_title = (
        "Очень длинный SEO заголовок превышающий семьдесят допустимых "
        "правилами знаков для поисковых систем"
    )
    raw_card = ProductCardOutput(
        seo_title=long_title,
        seo_description="Описание " * 80,
        key_specs={},
        search_queries=["q1", "q2", "q3"],
        commercial_block=CommercialBlock(
            target_audience="A", solved_problems="B"
        ),
    )
    sanitized = AntiHallucinationGuard.verify_and_sanitize(raw_card, item)
    assert len(sanitized.seo_title) <= 70
