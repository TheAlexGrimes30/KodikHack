from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = PROJECT_ROOT / ".env"

class Settings(BaseSettings):
    """
    Project settings
    """

    DB_NAME: str
    DB_USER: str
    DB_PASS: str
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432

    OLLAMA_BASE_URL: str = "http://127.0.0.1:11434"
    OLLAMA_MODEL: str = "qwen2.5:3b"
    OLLAMA_TEMPERATURE: float = 0.2
    OLLAMA_TIMEOUT: int = 60
    OLLAMA_EMBED_MODEL: str = "bge-m3"

    QDRANT_URL: str = "http://127.0.0.1:6333"
    QDRANT_COLLECTION: str = "external_knowledge_chunks"
    QDRANT_TIMEOUT: int = 15

    RAG_TOP_K: int = 8
    RAG_PREFETCH_LIMIT: int = 24
    RAG_CHUNK_SIZE: int = 800
    RAG_CHUNK_OVERLAP: int = 120

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def DATABASE_URL(self) -> str:
        """Async URL для SQLAlchemy + asyncpg."""

        return (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    @property
    def ALEMBIC_DATABASE_URL(self) -> str:
        """Sync URL для Alembic + psycopg2."""

        return (
            f"postgresql+psycopg2://{self.DB_USER}:{self.DB_PASS}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

settings = Settings()
