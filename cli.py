#!/usr/bin/env python3
import argparse
import asyncio
import json
import sys
from pathlib import Path

from src.models.product import ProductCardOutput
from src.services.generator import default_generator_service


def main():
    # Ensure UTF-8 output on Windows terminals
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        description="AI-помощник для подготовки карточек товаров B2B (КИПиА)"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--preset",
        type=int,
        choices=[0, 1, 2],
        help=(
            "Использовать один из предустановленных товаров Союз-Прибор "
            "(0: МК110, 1: ПМ01, 2: Неполный манометр)"
        ),
    )
    group.add_argument(
        "--input", type=str, help="Путь к файлу с входным JSON товара"
    )

    parser.add_argument(
        "--provider",
        type=str,
        default="ollama",
        choices=["ollama", "mock"],
        help="Используемый провайдер генерации (по умолчанию: ollama)",
    )
    parser.add_argument(
        "--format",
        type=str,
        default="markdown",
        choices=["markdown", "text", "json"],
        help="Формат вывода результата (по умолчанию: markdown)",
    )
    parser.add_argument(
        "--output", type=str, help="Сохранить результат в файл вместо stdout"
    )

    args = parser.parse_args()

    # Загрузка входных данных
    if args.preset is not None:
        samples_path = Path("data/samples.json")
        if not samples_path.exists():
            print(f"Ошибка: файл {samples_path} не найден.", file=sys.stderr)
            sys.exit(1)
        with open(samples_path, "r", encoding="utf-8") as f:
            presets = json.load(f)
        item_data = presets[args.preset]
        print(
            f"==> Загружен пресет {args.preset}: {item_data.get('name')}",
            file=sys.stderr,
        )
    else:
        input_path = Path(args.input)
        if not input_path.exists():
            print(f"Ошибка: файл {input_path} не найден.", file=sys.stderr)
            sys.exit(1)
        with open(input_path, "r", encoding="utf-8") as f:
            item_data = json.load(f)

    # Генерация карточки
    try:
        card: ProductCardOutput = asyncio.run(
            default_generator_service.generate_from_dict(
                item_data, provider_type=args.provider
            )
        )
    except (ValueError, RuntimeError) as e:
        print(f"Ошибка при формировании карточки: {e}", file=sys.stderr)
        sys.exit(1)

    # Форматирование вывода
    if args.format == "markdown":
        result_str = card.to_markdown()
    elif args.format == "text":
        result_str = card.to_plain_text()
    else:
        result_str = json.dumps(
            card.to_json_dict(), ensure_ascii=False, indent=2
        )

    if args.output:
        out_path = Path(args.output)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(result_str)
        print(
            f"==> Результат успешно сохранён в: {out_path.resolve()}",
            file=sys.stderr,
        )
    else:
        print(result_str)


if __name__ == "__main__":
    main()
