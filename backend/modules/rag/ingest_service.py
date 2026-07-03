import asyncio
import hashlib
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select

from backend.app.config import settings
from backend.db import IngestionRun, SourceCatalog, SourceChunk, SourceDocument
from backend.db.database import async_session_maker
from backend.modules.rag.chunking import TextChunker
from backend.modules.rag.embeddings import EmbeddingClient
from backend.modules.rag.qdrant_client import QdrantClient
from backend.modules.rag.schemas import RAGDocument
from backend.modules.rag.source_normalizers import normalize_text


class RAGIngestService:
    def __init__(
        self,
        embedding_client: EmbeddingClient | None = None,
        qdrant_client: QdrantClient | None = None,
        chunker: TextChunker | None = None,
    ) -> None:
        self.embedding_client = embedding_client or EmbeddingClient()
        self.qdrant_client = qdrant_client or QdrantClient()
        self.chunker = chunker or TextChunker()

    async def ingest_documents(self, documents: list[RAGDocument]) -> dict[str, int]:
        stats = {"docs_seen": len(documents), "docs_new": 0, "docs_updated": 0}
        grouped: dict[str, list[RAGDocument]] = {}
        for document in documents:
            grouped.setdefault(document.source_key, []).append(document)

        for source_key, source_docs in grouped.items():
            await self._ingest_source_group(source_key=source_key, documents=source_docs, stats=stats)

        return stats

    async def _ingest_source_group(
        self,
        *,
        source_key: str,
        documents: list[RAGDocument],
        stats: dict[str, int],
    ) -> None:
        async with async_session_maker() as session:
            source = await session.scalar(select(SourceCatalog).where(SourceCatalog.source_key == source_key))
            if source is None:
                source = SourceCatalog(
                    source_key=source_key,
                    title=source_key.replace("_", " ").title(),
                    source_type=documents[0].source_type,
                    base_url=documents[0].url,
                    vertical_key=documents[0].vertical_key,
                    country=documents[0].country,
                    language=documents[0].language,
                    trust_score=documents[0].trust_score,
                )
                session.add(source)
                await session.flush()

            run = IngestionRun(
                source_id=source.id,
                status="running",
                started_at=datetime.now(timezone.utc),
            )
            session.add(run)
            await session.flush()

            try:
                for document in documents:
                    updated = await self._upsert_document(session=session, source=source, document=document)
                    if updated:
                        stats["docs_updated"] += 1
                    else:
                        stats["docs_new"] += 1
                run.status = "completed"
            except Exception as exc:
                run.status = "failed"
                run.error_log = str(exc)
                raise
            finally:
                run.finished_at = datetime.now(timezone.utc)
                run.docs_seen = len(documents)
                run.docs_new = stats["docs_new"]
                run.docs_updated = stats["docs_updated"]
                await session.commit()

    async def _upsert_document(
        self,
        *,
        session: Any,
        source: SourceCatalog,
        document: RAGDocument,
    ) -> bool:
        normalized_text = normalize_text(document.content)
        content_hash = hashlib.sha256(normalized_text.encode("utf-8")).hexdigest()
        existing = await session.scalar(
            select(SourceDocument).where(
                SourceDocument.source_id == source.id,
                SourceDocument.url == document.url,
            )
        )
        is_update = existing is not None

        model = existing or SourceDocument(
            source_id=source.id,
            url=document.url,
            title=document.title,
            raw_text=normalized_text,
            content_hash=content_hash,
        )
        model.external_id = document.external_id
        model.title = document.title
        model.author = document.author
        model.published_at = document.published_at
        model.doc_type = document.doc_type
        model.raw_text = normalized_text
        model.summary = document.metadata.get("summary")
        model.content_hash = content_hash
        model.source_meta = {
            **document.metadata,
            "source_key": document.source_key,
            "source_type": document.source_type,
            "vertical_key": document.vertical_key,
            "risk_type": document.risk_type,
            "country": document.country,
            "language": document.language,
            "trust_score": document.trust_score,
            "title": document.title,
            "url": document.url,
            "published_at": document.published_at.isoformat() if document.published_at else None,
        }
        session.add(model)
        await session.flush()

        if is_update:
            existing_chunks = await session.scalars(
                select(SourceChunk).where(SourceChunk.document_id == model.id)
            )
            for chunk in existing_chunks:
                await session.delete(chunk)
            await session.flush()

        chunks = self.chunker.chunk_text(normalized_text)
        embeddings = await asyncio.to_thread(
            self.embedding_client.embed_texts,
            [chunk.text for chunk in chunks],
            settings.OLLAMA_EMBED_MODEL,
        )

        points: list[dict[str, Any]] = []
        for idx, chunk in enumerate(chunks):
            point_id = str(uuid.uuid4())
            session.add(
                SourceChunk(
                    document_id=model.id,
                    chunk_no=chunk.chunk_no,
                    text=chunk.text,
                    token_count=chunk.token_count,
                    embedding_model=settings.OLLAMA_EMBED_MODEL,
                    embedding_dim=len(embeddings[idx]) if idx < len(embeddings) else None,
                    qdrant_point_id=point_id,
                    chunk_meta={
                        "source_key": document.source_key,
                        "source_type": document.source_type,
                        "vertical_key": document.vertical_key,
                        "risk_type": document.risk_type,
                    },
                )
            )
            if idx < len(embeddings):
                points.append(
                    {
                        "id": point_id,
                        "vector": {"dense": embeddings[idx]},
                        "payload": {
                            "document_id": str(model.id),
                            "text": chunk.text,
                            "source_key": document.source_key,
                            "source_type": document.source_type,
                            "vertical_key": document.vertical_key,
                            "risk_type": document.risk_type,
                            "country": document.country,
                            "language": document.language,
                            "title": document.title,
                            "url": document.url,
                            "published_at": document.published_at.isoformat() if document.published_at else None,
                            "trust_score": document.trust_score,
                            "chunk_no": chunk.chunk_no,
                        },
                    }
                )

        if points:
            await asyncio.to_thread(
                self.qdrant_client.ensure_collection,
                vector_size=len(points[0]["vector"]["dense"]),
            )
            await asyncio.to_thread(self.qdrant_client.upsert_points, points)

        return is_update
