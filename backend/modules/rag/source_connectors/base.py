from abc import ABC, abstractmethod

from backend.modules.rag.schemas import RAGDocument


class SourceConnector(ABC):
    source_key: str

    @abstractmethod
    async def fetch_documents(self) -> list[RAGDocument]:
        raise NotImplementedError
