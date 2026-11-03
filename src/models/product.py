from __future__ import annotations
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, field_validator
import json

class ProductInput(BaseModel):
    """
    Входные данные о контрольно-измерительном приборе.
    """
    id: Optional[str] = Field(default=None, description="Идентификатор товара")
    name: str = Field(..., min_length=1, description="Название товара / прибора")
    manufacturer: Optional[str] = Field(default="", description="Производитель")
    specs: Dict[str, Any] = Field(default_factory=dict, description="Краткие характеристики")
    description: Optional[str] = Field(default="", description="Текстовое описание или фрагмент паспорта")

    @field_validator("name")
    def validate_name_not_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Название товара не может быть пустым")
        return v.strip()


class MissingFieldInfo(BaseModel):
    """
    Информация об отсутствующих или неполных характеристиках.
    """
    field_name: str
    message: str
    severity: str = "warning"  # warning, info, error


class CommercialBlock(BaseModel):
    """
    Commercial-блок для менеджера по продажам.
    """
    target_audience: str = Field(..., description="Кому подходит прибор (целевой сегмент, предприятия, специалисты)")
    solved_problems: str = Field(..., description="Какие производственные или коммерческие задачи решает")

    @field_validator("target_audience", "solved_problems", mode="before")
    def coerce_to_string(cls, v: Any) -> str:
        if isinstance(v, list):
            return ". ".join(str(x).strip() for x in v if str(x).strip())
        return str(v) if v is not None else ""


class ProductCardOutput(BaseModel):
    """
    Черновик карточки товара для B2B интернет-магазина КИПиА.
    """
    seo_title: str = Field(..., max_length=100, description="SEO-заголовок (целевая длина до 70 символов)")
    seo_description: str = Field(..., description="SEO-описание (целевой объём 800–1200 символов)")
    key_specs: Dict[str, str] = Field(..., description="Структурированный список ключевых характеристик")
    search_queries: List[str] = Field(..., min_length=1, max_length=10, description="3–5 поисковых запросов")
    commercial_block: CommercialBlock = Field(..., description="Блок для менеджера по продажам")
    missing_fields: List[MissingFieldInfo] = Field(default_factory=list, description="Предупреждения о недостающих данных")

    @field_validator("search_queries", mode="before")
    def clamp_search_queries(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            v = [v]
        if isinstance(v, list):
            cleaned = [str(x).strip() for x in v if str(x).strip()]
            return cleaned[:5] if len(cleaned) > 5 else cleaned
        return ["купить промышленное оборудование", "каталог КИПиА", "цена с ндс"]
    
    # Metadata metrics
    seo_title_length: int = Field(default=0)
    seo_description_length: int = Field(default=0)
    is_hallucination_free: bool = Field(default=True)

    def model_post_init(self, __context: Any) -> None:
        self.seo_title_length = len(self.seo_title)
        self.seo_description_length = len(self.seo_description)

    def to_markdown(self) -> str:
        """
        Форматирует карточку товара в чистый GitHub Flavored Markdown.
        """
        queries_md = "\n".join(f"- `{q}`" for q in self.search_queries)
        
        specs_md = "\n".join(
            f"| **{k}** | {v} |" for k, v in self.key_specs.items()
        )
        
        warnings_md = ""
        if self.missing_fields:
            warnings_lines = "\n".join(f"> ⚠️ **{m.field_name}**: {m.message}" for m in self.missing_fields)
            warnings_md = f"\n### ⚠️ Требуется уточнение данных\n{warnings_lines}\n"
            
        md = f"""# {self.seo_title}
*Длина заголовка: {self.seo_title_length} симв. (лимит: 70)*

## SEO-описание
{self.seo_description}
*Объём описания: {self.seo_description_length} симв. (целевой диапазон: 800–1200)*
{warnings_md}
## Ключевые технические характеристики
| Характеристика | Значение |
| :--- | :--- |
{specs_md}

## Поисковые запросы для продвижения
{queries_md}

## Commercial-блок для отдела продаж
- **Кому подходит прибор:** {self.commercial_block.target_audience}
- **Какие задачи решает:** {self.commercial_block.solved_problems}
"""
        return md.strip()

    def to_plain_text(self) -> str:
        """
        Форматирует карточку в структурированный читаемый текст для копирования в буфер.
        """
        queries_txt = "\n".join(f"  • {q}" for q in self.search_queries)
        specs_txt = "\n".join(f"  • {k}: {v}" for k, v in self.key_specs.items())
        
        warnings_txt = ""
        if self.missing_fields:
            warnings_txt = "ПРЕДУПРЕЖДЕНИЯ О НЕДОСТАТКЕ ДАННЫХ:\n" + "\n".join(
                f"  ! {m.field_name}: {m.message}" for m in self.missing_fields
            ) + "\n\n"
            
        txt = f"""=======================================================
SEO-ЗАГОЛОВОК ({self.seo_title_length} симв.):
{self.seo_title}
=======================================================

SEO-ОПИСАНИЕ ({self.seo_description_length} симв.):
{self.seo_description}

{warnings_txt}КЛЮЧЕВЫЕ ХАРАКТЕРИСТИКИ:
{specs_txt}

ПОИСКОВЫЕ ЗАПРОСЫ:
{queries_txt}

ДЛЯ ОТДЕЛА ПРОДАЖ:
Целевая аудитория: {self.commercial_block.target_audience}
Решаемые задачи: {self.commercial_block.solved_problems}
======================================================="""
        return txt.strip()

    def to_json_dict(self) -> Dict[str, Any]:
        """
        Возвращает чистый словарь структуры JSON.
        """
        return self.model_dump()
