from pathlib import Path
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from backend.modules.rag.ingest_service import RAGIngestService
from backend.modules.rag.retriever import HybridEnvironmentRetriever
from backend.modules.rag.source_connectors.local_folder import LocalFolderConnector


router = APIRouter(prefix="/rag", tags=["rag"])


class RagSearchRequest(BaseModel):
    query: str
    limit: int = Field(default=5, ge=1, le=20)
    project_context: dict[str, Any] = Field(default_factory=dict)
    assumptions: list[dict[str, Any]] = Field(default_factory=list)


class RagIngestRequest(BaseModel):
    folder: str = "RAG_BASE"


@router.post("/search")
async def rag_search(payload: RagSearchRequest) -> dict[str, Any]:
    retriever = HybridEnvironmentRetriever()
    sources = await retriever.retrieve(
        query=payload.query,
        project_context=payload.project_context,
        assumptions=payload.assumptions,
        limit=payload.limit,
    )
    return {
        "query": payload.query,
        "count": len(sources),
        "items": [source.model_dump(mode="json") for source in sources],
    }


@router.post("/ingest/local")
async def ingest_local_folder(payload: RagIngestRequest) -> dict[str, Any]:
    folder = Path(payload.folder)
    if not folder.exists() and payload.folder == "RAG_BASE":
        fallback = Path("rag_base")
        if fallback.exists():
            folder = fallback

    connector = LocalFolderConnector(folder)
    documents = await connector.fetch_documents()

    service = RAGIngestService()
    stats = await service.ingest_documents(documents)

    return {
        "folder": str(folder),
        "documents_loaded": len(documents),
        "stats": stats,
    }
