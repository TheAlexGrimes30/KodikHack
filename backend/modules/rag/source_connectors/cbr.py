from backend.modules.rag.schemas import RAGDocument
from backend.modules.rag.source_connectors.base import SourceConnector


class CBRSourceConnector(SourceConnector):
    source_key = "cbr"

    async def fetch_documents(self) -> list[RAGDocument]:
        return []
