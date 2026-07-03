from backend.modules.rag.schemas import RAGDocument
from backend.modules.rag.source_connectors.base import SourceConnector


class RosstatSourceConnector(SourceConnector):
    source_key = "rosstat"

    async def fetch_documents(self) -> list[RAGDocument]:
        return []
