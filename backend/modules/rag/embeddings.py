import json
from dataclasses import dataclass
from urllib import request as urllib_request
from urllib.error import HTTPError, URLError

from backend.app.config import settings


@dataclass(frozen=True)
class EmbeddingSettings:
    base_url: str = settings.OLLAMA_BASE_URL
    model: str = settings.OLLAMA_EMBED_MODEL
    timeout: int = settings.OLLAMA_TIMEOUT


class EmbeddingClient:
    def __init__(self, embed_settings: EmbeddingSettings | None = None) -> None:
        self.settings = embed_settings or EmbeddingSettings()

    def embed_texts(self, texts: list[str], model: str | None = None) -> list[list[float]]:
        clean_texts = [text.strip() for text in texts if text and text.strip()]
        if not clean_texts:
            return []

        payload = {
            "model": model or self.settings.model,
            "input": clean_texts,
        }
        req = urllib_request.Request(
            url=f"{self.settings.base_url}/api/embed",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib_request.urlopen(req, timeout=self.settings.timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
                embeddings = data.get("embeddings") or []
                return [list(map(float, item)) for item in embeddings if isinstance(item, list)]
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
            return []
        except Exception:
            return []

    def embed_query(self, text: str, model: str | None = None) -> list[float]:
        embeddings = self.embed_texts([text], model=model)
        return embeddings[0] if embeddings else []
