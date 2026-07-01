from pathlib import Path
from typing import Any


def load_prompt(file_path: str | Path) -> str:
    return Path(file_path).read_text(encoding="utf-8")

def render_prompt(template: str, **kwargs: Any) -> str:
    result = template
    for key, value in kwargs.items():
        result = result.replace("{{ " + key + " }}", str(value))
        result = result.replace("{{" + key + "}}", str(value))
    return result
