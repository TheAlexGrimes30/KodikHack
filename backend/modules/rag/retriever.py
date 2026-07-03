import asyncio
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select

from backend.app.config import settings
from backend.db.database import async_session_maker
from backend.db.enviroment_events import EnvironmentEvent
from backend.db.failure_cases import FailureCase
from backend.db.industry_benchmarks import IndustryBenchmark
from backend.db.macro_indicators import MacroIndicator
from backend.modules.agents.enviroment.schemas import EnvironmentSource
from backend.modules.rag.embeddings import EmbeddingClient
from backend.modules.rag.qdrant_client import QdrantClient
from backend.modules.rag.reranker import HeuristicReranker


class StructuredSignalRetriever:
    async def retrieve(
        self,
        *,
        project_context: dict[str, Any],
        limit: int,
    ) -> list[EnvironmentSource]:
        try:
            async with async_session_maker() as session:
                results: list[EnvironmentSource] = []
                vertical_key = project_context.get("vertical_key")

                statements = [
                    select(EnvironmentEvent).order_by(EnvironmentEvent.happened_at.desc().nullslast()).limit(limit),
                    select(MacroIndicator).order_by(MacroIndicator.observed_at.desc()).limit(limit),
                    select(IndustryBenchmark).order_by(IndustryBenchmark.captured_at.desc()).limit(limit),
                ]
                if vertical_key:
                    statements.append(
                        select(FailureCase)
                        .where(FailureCase.vertical_key == vertical_key)
                        .limit(limit)
                    )
                else:
                    statements.append(select(FailureCase).limit(limit))

                for statement in statements:
                    rows = await session.execute(statement)
                    for row in rows.scalars():
                        item = self._to_source(row)
                        if item:
                            results.append(item)

                return results[:limit]
        except Exception:
            return []

    def _to_source(self, row: Any) -> EnvironmentSource | None:
        if isinstance(row, EnvironmentEvent):
            return EnvironmentSource(
                title=row.title,
                source_type="structured_event",
                content=row.body or row.title,
                published_at=(
                    datetime.combine(row.happened_at, datetime.min.time(), tzinfo=timezone.utc)
                    if row.happened_at
                    else None
                ),
                trust_score=0.9,
                metadata={
                    "risk_type": row.category,
                    "impact_hint": row.impact_hint,
                    "feed_key": row.feed_key,
                },
            )
        if isinstance(row, MacroIndicator):
            return EnvironmentSource(
                title=f"Macro indicator: {row.indicator}",
                source_type="structured_macro",
                content=f"{row.indicator}: {row.value} on {row.observed_at}",
                published_at=datetime.combine(row.observed_at, datetime.min.time(), tzinfo=timezone.utc),
                trust_score=0.95,
                metadata={
                    "risk_type": "macro",
                    "indicator": row.indicator,
                    "feed_key": row.feed_key,
                },
            )
        if isinstance(row, IndustryBenchmark):
            return EnvironmentSource(
                title=f"Benchmark: {row.metric_key}",
                source_type="benchmark",
                content=f"{row.metric_key}={row.value} {row.unit or ''}".strip(),
                published_at=row.captured_at,
                trust_score=0.85,
                metadata={
                    "risk_type": "benchmark",
                    "vertical_key": row.vertical_key,
                    "source": row.source,
                },
            )
        if isinstance(row, FailureCase):
            return EnvironmentSource(
                title=row.title,
                source_type="failure_case",
                content=" ".join(part for part in [row.summary, row.outcome] if part),
                url=row.source,
                trust_score=0.75,
                metadata={
                    "risk_type": row.risk_type,
                    "vertical_key": row.vertical_key,
                },
            )
        return None


class QdrantKnowledgeRetriever:
    def __init__(
        self,
        embedding_client: EmbeddingClient | None = None,
        qdrant_client: QdrantClient | None = None,
        reranker: HeuristicReranker | None = None,
    ) -> None:
        self.embedding_client = embedding_client or EmbeddingClient()
        self.qdrant_client = qdrant_client or QdrantClient()
        self.reranker = reranker or HeuristicReranker()

    async def retrieve(
        self,
        *,
        query: str,
        project_context: dict[str, Any],
        limit: int,
    ) -> list[EnvironmentSource]:
        try:
            dense_vector = await asyncio.to_thread(self.embedding_client.embed_query, query)
            if not dense_vector:
                return []

            query_filter = self._build_filter(project_context)
            chunks = await asyncio.to_thread(
                self.qdrant_client.query_dense,
                dense_vector=dense_vector,
                limit=max(limit, settings.RAG_TOP_K),
                query_filter=query_filter,
            )
            ranked = self.reranker.rerank(query, chunks, limit)
            return [
                EnvironmentSource(
                    title=item.title or "Knowledge chunk",
                    source_type=item.source_type or "knowledge_chunk",
                    content=item.text,
                    url=item.url,
                    published_at=item.published_at,
                    trust_score=item.trust_score,
                    metadata={
                        **item.payload,
                        "risk_type": item.risk_type,
                        "source_key": item.source_key,
                        "retrieval_score": item.score,
                    },
                )
                for item in ranked
                if item.text
            ]
        except Exception:
            return []

    def _build_filter(self, project_context: dict[str, Any]) -> dict[str, Any] | None:
        must: list[dict[str, Any]] = []
        vertical_key = project_context.get("vertical_key")
        geography = project_context.get("geography")

        if vertical_key:
            must.append({"key": "vertical_key", "match": {"value": vertical_key}})
        if geography:
            must.append({"key": "country", "match": {"value": geography}})

        return {"must": must} if must else None


class HybridEnvironmentRetriever:
    def __init__(
        self,
        structured: StructuredSignalRetriever | None = None,
        knowledge: QdrantKnowledgeRetriever | None = None,
    ) -> None:
        self.structured = structured or StructuredSignalRetriever()
        self.knowledge = knowledge or QdrantKnowledgeRetriever()

    async def retrieve(
        self,
        *,
        query: str,
        project_context: dict[str, Any],
        assumptions: list[dict[str, Any]],
        limit: int = 5,
    ) -> list[EnvironmentSource]:
        structured_sources, knowledge_sources = await asyncio.gather(
            self.structured.retrieve(project_context=project_context, limit=limit),
            self.knowledge.retrieve(query=query, project_context=project_context, limit=limit),
        )

        merged = self._merge_sources(structured_sources + knowledge_sources)
        if merged:
            return merged[:limit]

        return self._fallback_sources(limit)

    def _merge_sources(self, sources: list[EnvironmentSource]) -> list[EnvironmentSource]:
        grouped: dict[str, EnvironmentSource] = {}
        for source in sources:
            key = source.url or f"{source.source_type}:{source.title}:{source.content[:80]}"
            existing = grouped.get(key)
            if existing is None or float(source.trust_score or 0.0) > float(existing.trust_score or 0.0):
                grouped[key] = source

        ranked = sorted(
            grouped.values(),
            key=lambda item: (float(item.trust_score or 0.0), item.published_at or datetime.min.replace(tzinfo=timezone.utc)),
            reverse=True,
        )
        return ranked

    def _fallback_sources(self, limit: int) -> list[EnvironmentSource]:
        templates = [
            EnvironmentSource(
                title="Demand weakness baseline",
                source_type="fallback",
                content="Early signals can overstate true willingness to pay; validate with stronger commitment signals.",
                trust_score=0.45,
                metadata={"risk_type": "weak_demand"},
            ),
            EnvironmentSource(
                title="Acquisition cost pressure baseline",
                source_type="fallback",
                content="Acquisition economics may worsen before retention and monetization are proven.",
                trust_score=0.4,
                metadata={"risk_type": "cac_growth"},
            ),
            EnvironmentSource(
                title="Runway pressure baseline",
                source_type="fallback",
                content="A limited runway compresses experimentation cycles and increases the cost of false positives.",
                trust_score=0.4,
                metadata={"risk_type": "runway"},
            ),
        ]
        return templates[:limit]
