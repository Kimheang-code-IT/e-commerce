from __future__ import annotations

import re
from typing import Any

CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def clean_text(value: str) -> str:
    """Trim user text and remove control characters that can poison logs/CSV/UI output."""
    return CONTROL_CHARS_RE.sub("", value).strip()


def clean_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    return clean_text(value)


def clean_string_list(values: list[Any]) -> list[str]:
    cleaned: list[str] = []
    for value in values:
        item = clean_text(str(value))
        if item:
            cleaned.append(item)
    return cleaned
