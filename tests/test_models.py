import pytest

from src.models.product import CommercialBlock, ProductCardOutput, ProductInput


def test_product_input_valid():
    data = {
        "name": "Манометр показывающий DM 02",
        "manufacturer": "Манотомь",
        "specs": {"диапазон": "0-1.6 МПа"},
        "description": "Прибор для измерения давления",
    }
    item = ProductInput(**data)
    assert item.name == "Манометр показывающий DM 02"
    assert item.manufacturer == "Манотомь"
    assert item.specs["диапазон"] == "0-1.6 МПа"


def test_product_input_empty_name_raises():
    with pytest.raises(ValueError):
        ProductInput(name="   ", manufacturer="Тест")


def test_product_card_output_metrics():
    card = ProductCardOutput(
        seo_title="Краткий заголовок",
        seo_description="A" * 850,
        key_specs={"интерфейс": "RS-485"},
        search_queries=["запрос 1", "запрос 2", "запрос 3"],
        commercial_block=CommercialBlock(
            target_audience="Инженеры", solved_problems="Автоматизация"
        ),
    )
    assert card.seo_title_length == len("Краткий заголовок")
    assert card.seo_description_length == 850
    assert "# Краткий заголовок" in card.to_markdown()
    assert "SEO-ЗАГОЛОВОК" in card.to_plain_text()


def test_product_card_output_coerces_list_specs_and_commercial():
    card = ProductCardOutput(
        seo_title="Модем ОВЕН ПМ01",
        seo_description="A" * 850,
        key_specs={
            "интерфейсы связи": ["RS-232", "RS-485"],
            "поддержка SIM-карт": ["1.8 В", "3.0 В"],
        },
        search_queries=["запрос 1", "запрос 2", "запрос 3"],
        commercial_block=CommercialBlock(
            target_audience=["Инженеры", "Интеграторы"],
            solved_problems="Автоматизация",
        ),
        missing_fields=["напряжение питания"],
    )
    assert card.key_specs["интерфейсы связи"] == "RS-232, RS-485"
    assert card.key_specs["поддержка SIM-карт"] == "1.8 В, 3.0 В"
    assert "Инженеры" in card.commercial_block.target_audience
    assert card.missing_fields[0].field_name == "напряжение питания"
