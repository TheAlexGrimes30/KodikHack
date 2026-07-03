from backend.modules.rag.schemas import RAGDocument
from backend.modules.rag.source_connectors.base import SourceConnector


class VCArticlesConnector(SourceConnector):
    source_key = "vc_articles"

    async def fetch_documents(self) -> list[RAGDocument]:
        return []
