from backend.modules.rag.schemas import RAGDocument
from backend.modules.rag.source_connectors.base import SourceConnector


class CompetitorPagesConnector(SourceConnector):
    source_key = "competitor_pages"

    async def fetch_documents(self) -> list[RAGDocument]:
        return []
