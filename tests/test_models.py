import pytest
from src.models.product import ProductInput, ProductCardOutput, CommercialBlock, MissingFieldInfo

def test_product_input_valid():
    data = {
        "name": "Манометр показывающий DM 02",
        "manufacturer": "Манотомь",
        "specs": {"диапазон": "0-1.6 МПа"},
        "description": "Прибор для измерения давления"
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
            target_audience="Инженеры",
            solved_problems="Автоматизация"
        )
    )
    assert card.seo_title_length == len("Краткий заголовок")
    assert card.seo_description_length == 850
    assert "# Краткий заголовок" in card.to_markdown()
    assert "SEO-ЗАГОЛОВОК" in card.to_plain_text()
