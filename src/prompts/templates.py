from __future__ import annotations

from typing import Any

from src.texts import TEXTS

SYSTEM_PROMPT: str = TEXTS["prompts"]["system_prompt"]
USER_PROMPT_TEMPLATE: str = TEXTS["prompts"]["user_prompt_template"]


def format_user_prompt(data: dict[str, Any]) -> str:
    specs = data.get("specs", {})
    if isinstance(specs, dict):
        specs_formatted = "\n".join(f"- {k}: {v}" for k, v in specs.items())
    elif isinstance(specs, list):
        specs_formatted = "\n".join(f"- {item}" for item in specs)
    else:
        specs_formatted = str(specs)

    defaults = TEXTS["defaults"]
    return USER_PROMPT_TEMPLATE.format(
        name=data.get("name") or defaults["unspecified_name"],
        manufacturer=data.get("manufacturer")
        or defaults["unspecified_vendor"],
        specs_formatted=specs_formatted
        if specs_formatted
        else defaults["no_specs_label"],
        description=data.get("description") or defaults["no_desc_label"],
    )
