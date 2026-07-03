import html
import re


def normalize_text(raw_text: str) -> str:
    text = html.unescape(raw_text or "")
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()
