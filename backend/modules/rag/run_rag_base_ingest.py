import asyncio
from pathlib import Path

from backend.modules.rag.ingest_service import RAGIngestService
from backend.modules.rag.source_connectors.local_folder import LocalFolderConnector


async def main() -> None:
    folder = Path("RAG_BASE")
    if not folder.exists():
        folder = Path("rag_base")
    connector = LocalFolderConnector(folder)
    documents = await connector.fetch_documents()

    service = RAGIngestService()
    stats = await service.ingest_documents(documents)

    print(f"Loaded documents: {len(documents)}")
    print(f"Stats: {stats}")


if __name__ == "__main__":
    asyncio.run(main())
