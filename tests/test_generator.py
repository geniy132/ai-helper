import pytest
from src.services.generator import CardGenerationService
from src.services.providers.mock_provider import MockLLMProvider

@pytest.mark.asyncio
async def test_card_generation_pipeline():
    service = CardGenerationService(provider=MockLLMProvider())
    payload = {
        "name": "Модуль дискретного ввода/вывода ОВЕН МК110-224.8Д.4Р [М01]",
        "manufacturer": "ОВЕН",
        "specs": {
            "интерфейс связи": "RS-485",
            "количество дискретных входов": "8",
            "количество дискретных выходов": "4",
            "напряжение питания": "220 В"
        },
        "description": "Модуль предназначен для ввода и вывода сигналов в сеть RS-485."
    }

    card = await service.generate_from_dict(payload)
    
    # Проверка строгих требований ТЗ
    assert len(card.seo_title) <= 70, f"SEO title len: {len(card.seo_title)}"
    assert 800 <= len(card.seo_description) <= 1200, f"SEO desc len: {len(card.seo_description)}"
    assert len(card.search_queries) >= 3
    assert card.commercial_block.target_audience
    assert card.commercial_block.solved_problems
    assert "RS-485" in card.key_specs["интерфейс связи"]
