import json
import os
import urllib
from dataclasses import dataclass


@dataclass(frozen=True)
class OllamaSettings:
    base_url: str = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    model: str = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
    temperature: float = float(os.getenv("OLLAMA_TEMPERATURE", "0.2"))
    timeout: int = int(os.getenv("OLLAMA_TIMEOUT", "60"))

class LLMClient:
    """Тонкий клиент LLM.

    Сейчас совместим с прототипом Kodik: локальная Ollama, POST /api/generate,
    fallback при недоступности модели.
    """

    def __init__(self, settings: OllamaSettings | None = None) -> None:
        self.settings = settings or OllamaSettings()

    def generate(self, system_prompt: str, user_prompt: str, *, fallback: str) -> str:
        prompt = f"{system_prompt.strip()}\n\n{user_prompt.strip()}"
        payload = {
            "model": self.settings.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": self.settings.temperature},
        }
        request = urllib.request.Request(
            f"{self.settings.base_url}/api/generate",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.settings.timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
                text = str(data.get("response") or "").strip()
                return text or fallback
        except Exception:
            return fallback