import re

from backend.app.config import settings
from backend.modules.rag.schemas import ChunkedDocument


class TextChunker:
    def __init__(self, chunk_size: int | None = None, overlap: int | None = None) -> None:
        self.chunk_size = chunk_size or settings.RAG_CHUNK_SIZE
        self.overlap = overlap or settings.RAG_CHUNK_OVERLAP

    def chunk_text(self, text: str) -> list[ChunkedDocument]:
        normalized = re.sub(r"\s+", " ", text or "").strip()
        if not normalized:
            return []

        words = normalized.split(" ")
        if len(words) <= self.chunk_size:
            return [ChunkedDocument(chunk_no=0, text=normalized, token_count=len(words))]

        chunks: list[ChunkedDocument] = []
        start = 0
        step = max(1, self.chunk_size - self.overlap)
        chunk_no = 0

        while start < len(words):
            end = min(len(words), start + self.chunk_size)
            chunk_words = words[start:end]
            chunk_text = " ".join(chunk_words).strip()
            if chunk_text:
                chunks.append(
                    ChunkedDocument(
                        chunk_no=chunk_no,
                        text=chunk_text,
                        token_count=len(chunk_words),
                    )
                )
                chunk_no += 1
            if end >= len(words):
                break
            start += step

        return chunks
