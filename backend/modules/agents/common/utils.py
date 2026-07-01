import json
import re
from decimal import Decimal
from typing import Any


def decimal_or_none(value: Any) -> Decimal | None:
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value))
    except Exception:
        return None

def extract_json_object(text: str) -> dict[str, Any] | None:
    """Пытается вытащить JSON из ответа LLM.

    Заглушки остаются: если модель вернула невалидный JSON, агент использует
    fallback-структуру. Для хакатона этого достаточно.
    """

    if not text:
        return None

    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
    cleaned = re.sub(r"```$", "", cleaned).strip()

    try:
        parsed = json.loads(cleaned)
        return parsed if isinstance(parsed, dict) else None
    except Exception:
        pass

    match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
    if not match:
        return None

    try:
        parsed = json.loads(match.group(0))
        return parsed if isinstance(parsed, dict) else None
    except Exception:
        return None
