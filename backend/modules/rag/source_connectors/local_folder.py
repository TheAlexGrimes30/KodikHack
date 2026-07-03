from pathlib import Path

from backend.modules.rag.extractors import LocalRagBaseExtractor
from backend.modules.rag.schemas import RAGDocument
from backend.modules.rag.source_connectors.base import SourceConnector


class LocalFolderConnector(SourceConnector):
    source_key = "rag_base_local"

    def __init__(self, folder_path: str | Path) -> None:
        self.folder_path = Path(folder_path)
        self.extractor = LocalRagBaseExtractor()

    async def fetch_documents(self) -> list[RAGDocument]:
        documents: list[RAGDocument] = []
        for path in sorted(self.folder_path.glob("*")):
            if not path.is_file():
                continue
            document = self.extractor.extract_file(path)
            if document is not None:
                documents.append(document)
        return documents
