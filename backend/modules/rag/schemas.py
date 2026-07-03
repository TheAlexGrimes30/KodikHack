from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class RetrievedChunk(BaseModel):
    point_id: str
    score: float
    text: str
    source_key: str | None = None
    title: str | None = None
    url: str | None = None
    published_at: datetime | None = None
    source_type: str | None = None
    risk_type: str | None = None
    vertical_key: str | None = None
    trust_score: float | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class RAGDocument(BaseModel):
    external_id: str | None = None
    url: str
    title: str
    content: str
    source_key: str
    source_type: str
    vertical_key: str | None = None
    risk_type: str | None = None
    country: str | None = None
    language: str | None = None
    published_at: datetime | None = None
    author: str | None = None
    doc_type: str = "article"
    trust_score: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ChunkedDocument(BaseModel):
    chunk_no: int
    text: str
    token_count: int
    metadata: dict[str, Any] = Field(default_factory=dict)
