import json
from dataclasses import dataclass

from urllib import request as urllib_request
from urllib.error import URLError, HTTPError

from backend.app.config import settings


@dataclass(frozen=True)
class OllamaSettings:
    base_url: str = settings.OLLAMA_BASE_URL
    model: str = settings.OLLAMA_MODEL
    temperature: float = settings.OLLAMA_TEMPERATURE
    timeout: int = settings.OLLAMA_TIMEOUT


class LLMClient:
    """Тонкий клиент для локальной Ollama."""

    def __init__(self, ollama_settings: OllamaSettings | None = None) -> None:
        self.settings = ollama_settings or OllamaSettings()

    def generate(self, system_prompt: str, user_prompt: str, *, fallback: str) -> str:
        prompt = f"{system_prompt.strip()}\n\n{user_prompt.strip()}"

        payload = {
            "model": self.settings.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.settings.temperature,
            },
        }

        req = urllib_request.Request(
            url=f"{self.settings.base_url}/api/generate",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib_request.urlopen(req, timeout=self.settings.timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
                text = str(data.get("response") or "").strip()
                return text or fallback

        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
            return fallback

        except Exception:
            return fallback
