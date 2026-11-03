from __future__ import annotations

"""
Централизованные константы проекта: лимиты ТЗ, пороги валидации и тайминги.
"""

# Лимиты длины SEO по ТЗ
SEO_TITLE_MAX_LEN = 70
SEO_DESC_MIN_LEN = 800
SEO_DESC_MAX_LEN = 1200
SEO_DESC_TRUNCATE_TARGET = 1180

# Ограничения по поисковым запросам
SEARCH_QUERIES_MIN = 3
SEARCH_QUERIES_MAX = 5
SEARCH_QUERIES_CLAMP = 5

# Пороги аудита входных данных
MIN_DESCRIPTION_LEN_FOR_AUDIT = 30

# Сетевые параметры и генерация
DEFAULT_TEMPERATURE = 0.2
DEFAULT_TIMEOUT_SEC = 60.0

# Системные маркеры отсутствия данных
DATA_NOT_FOUND_LABEL = "данных нет"
DATA_UNVERIFIED_SUFFIX = "требует уточнения: нет в паспорте"
